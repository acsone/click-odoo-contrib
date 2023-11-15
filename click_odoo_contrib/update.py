#!/usr/bin/env python
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import logging
import os
import threading
from contextlib import closing, contextmanager
from datetime import timedelta
from time import sleep

import click
import click_odoo
import psycopg2
from click_odoo import OdooEnvironment, odoo
from manifestoo_core.core_addons import get_core_addons
from manifestoo_core.odoo_series import OdooSeries

from ._addon_hash import addon_hash
from ._dbutils import advisory_lock

_logger = logging.getLogger(__name__)


PARAM_INSTALLED_CHECKSUMS = "module_auto_update.installed_checksums"
PARAM_EXCLUDE_PATTERNS = "module_auto_update.exclude_patterns"
DEFAULT_EXCLUDE_PATTERNS = "*.pyc,*.pyo,i18n/*.pot,i18n_extra/*.pot,static/*,tests/*"


class DbLockWatcher(threading.Thread):
    def __init__(self, database, max_seconds):
        super().__init__()
        self.daemon = True
        self.database = database
        self.max_seconds = max_seconds
        self.aborted = False
        self.watching = False

    def stop(self):
        self.watching = False

    def run(self):
        """Watch DB while another process is updating Odoo.

        This method will query :param:`database` to see if there are DB locks.
        If a lock longer than :param:`max_seconds` is detected, it will be
        terminated and an exception will be raised.

        :param str database:
            Name of the database that is being updated in parallel.

        :param float max_seconds:
            Max length of DB lock allowed.
        """
        _logger.info("Starting DB lock watcher")
        beat = self.max_seconds / 3
        max_td = timedelta(seconds=self.max_seconds)
        own_pid_query = "SELECT pg_backend_pid()"
        # SQL explained in https://wiki.postgresql.org/wiki/Lock_Monitoring
        locks_query = """
            SELECT
                pg_stat_activity.datname,
                pg_class.relname,
                pg_locks.transactionid,
                pg_locks.mode,
                pg_locks.granted,
                pg_stat_activity.usename,
                pg_stat_activity.query,
                pg_stat_activity.query_start,
                AGE(NOW(), pg_stat_activity.query_start) AS age,
                pg_stat_activity.pid
            FROM
                pg_stat_activity
                JOIN pg_locks ON pg_locks.pid = pg_stat_activity.pid
                JOIN pg_class ON pg_class.oid = pg_locks.relation
            WHERE
                NOT pg_locks.granted
                AND pg_stat_activity.datname = %s
            ORDER BY pg_stat_activity.query_start
        """
        # See https://stackoverflow.com/a/35319598/1468388
        terminate_session = "SELECT pg_terminate_backend(%s)"
        params = odoo.sql_db.connection_info_for(self.database)[1]
        # Need a separate raw psycopg2 cursor without transactioning to avoid
        # weird concurrency errors; this cursor will only trigger SELECTs, and
        # it needs to access current Postgres server status, monitoring other
        # transactions' status, so running inside a normal, transactioned,
        # Odoo cursor would block such monitoring and, after all, offer no
        # additional protection
        with closing(psycopg2.connect(**params)) as watcher_conn:
            watcher_conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
            )
            self.watching = True
            while self.watching:
                # Wait some time before checking locks
                sleep(beat)
                # Ensure no long blocking queries happen
                with closing(
                    watcher_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                ) as watcher_cr:
                    if _logger.level <= logging.DEBUG:
                        watcher_cr.execute(own_pid_query)
                        watcher_pid = watcher_cr.fetchone()[0]
                        _logger.debug(
                            "DB lock watcher running with postgres PID %d", watcher_pid
                        )
                    watcher_cr.execute(locks_query, (self.database,))
                    locks = watcher_cr.fetchall()
                    if locks:
                        _logger.warning("%d locked queries found", len(locks))
                        _logger.info("Query details: %r", locks)
                    for row in locks:
                        if row["age"] > max_td:
                            # Terminate the query to abort the parallel update
                            _logger.error(
                                "Long locked query detected; aborting update cursor "
                                "with PID %d...",
                                row["pid"],
                            )
                            self.aborted = True
                            watcher_cr.execute(terminate_session, (row["pid"],))


def _get_param(cr, key, default=None):
    cr.execute("SELECT value FROM ir_config_parameter WHERE key=%s", (key,))
    r = cr.fetchone()
    if r:
        return r[0]
    else:
        return default


def _set_param(cr, key, value):
    cr.execute(
        "UPDATE ir_config_parameter SET value=%s, write_date=now() AT TIME ZONE 'UTC' "
        "WHERE key=%s",
        (value, key),
    )
    if not cr.rowcount:
        cr.execute(
            "INSERT INTO ir_config_parameter (key, value, create_date, write_date) "
            "VALUES (%s, %s, now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC')",
            (key, value),
        )


def _load_installed_checksums(cr):
    value = _get_param(cr, PARAM_INSTALLED_CHECKSUMS)
    if value:
        return json.loads(value)
    else:
        return {}


def _save_installed_checksums(cr, ignore_addons=None):
    checksums = {}
    cr.execute("SELECT name FROM ir_module_module WHERE state='installed'")
    for (module_name,) in cr.fetchall():
        if ignore_addons and module_name in ignore_addons:
            continue
        checksums[module_name] = _get_checksum_dir(cr, module_name)
    _set_param(cr, PARAM_INSTALLED_CHECKSUMS, json.dumps(checksums))
    _logger.info("Database updated, new checksums stored")


def _get_checksum_dir(cr, module_name):
    exclude_patterns = _get_param(cr, PARAM_EXCLUDE_PATTERNS, DEFAULT_EXCLUDE_PATTERNS)
    exclude_patterns = [p.strip() for p in exclude_patterns.split(",")]
    cr.execute("SELECT code FROM res_lang WHERE active")
    keep_langs = [r[0] for r in cr.fetchall()]

    module_path = odoo.modules.module.get_module_path(module_name)
    if module_path and os.path.isdir(module_path):
        checksum_dir = addon_hash(module_path, exclude_patterns, keep_langs)
    else:
        checksum_dir = False

    return checksum_dir


def _get_modules_to_update(cr, ignore_addons=None):
    if ignore_addons is None:
        ignore_addons = []
    modules_to_update = []
    checksums = _load_installed_checksums(cr)
    cr.execute(
        "SELECT name FROM ir_module_module "
        "WHERE state in ('installed', 'to upgrade')"
    )
    for (module_name,) in cr.fetchall():
        if not _is_installable(module_name):
            # if the module is not installable, do not try to update it
            continue
        if module_name in ignore_addons:
            continue
        if _get_checksum_dir(cr, module_name) != checksums.get(module_name):
            modules_to_update.append(module_name)
    return modules_to_update


def _is_installable(module_name):
    try:
        if odoo.release.version_info < (16, 0):
            manifest = odoo.modules.load_information_from_description_file(module_name)
        else:
            manifest = odoo.modules.get_manifest(module_name)
        return manifest["installable"]
    except Exception:
        # load_information_from_description_file populates default value
        # so the exception would be KeyError if the module does not exist
        # in addons path, or an error parsing __manifest__.py. In either
        # case the module will not be installable.
        return False


def _update_db_nolock(
    conn,
    database,
    update_all,
    i18n_overwrite,
    watcher=None,
    list_only=False,
    ignore_addons=None,
):
    to_update = odoo.tools.config["update"]
    if update_all:
        to_update["base"] = 1
    else:
        with conn.cursor() as cr:
            for module_name in _get_modules_to_update(cr, ignore_addons):
                to_update[module_name] = 1
        if to_update:
            _logger.info(
                "Updating addons for their hash changed: %s.",
                ",".join(to_update.keys()),
            )
    if list_only:
        odoo.tools.config["update"] = {}
        _logger.info("List-only selected, update is not performed.")
        return
    if not to_update:
        _logger.info("No module needs updating, update is not performed.")
        return
    if i18n_overwrite:
        odoo.tools.config["overwrite_existing_translations"] = True
    odoo.modules.registry.Registry.new(database, update_module=True)
    if watcher and watcher.aborted:
        # If you get here, the updating session has been terminated and it
        # somehow has recovered by opening a new cursor and continuing;
        # that's very unlikely, but just in case some paranoid module
        # happens to update, let's just make sure the exit code for
        # this script indicates always a failure
        raise click.Abort("Update aborted by watcher, check logs")
    with conn.cursor() as cr:
        _save_installed_checksums(cr, ignore_addons)


def _update_db(
    database,
    update_all,
    i18n_overwrite,
    watcher=None,
    list_only=False,
    ignore_addons=None,
):
    conn = odoo.sql_db.db_connect(database)
    with conn.cursor() as cr, advisory_lock(cr, "click-odoo-update/" + database):
        _update_db_nolock(
            conn,
            database,
            update_all,
            i18n_overwrite,
            watcher,
            list_only,
            ignore_addons,
        )


@contextmanager
def OdooEnvironmentWithUpdate(database, ctx, **kwargs):
    # Watch for database locks while Odoo updates
    watcher = None
    if ctx.params["watcher_max_seconds"] > 0:
        watcher = DbLockWatcher(database, ctx.params["watcher_max_seconds"])
        watcher.start()
    ignore_addons = set()
    if ctx.params["ignore_addons"]:
        ignore_addons.update(ctx.params["ignore_addons"].strip().split(","))
    if ctx.params["ignore_core_addons"]:
        ignore_addons.update(get_core_addons(OdooSeries(odoo.release.series)))
    if ignore_addons and ctx.params["update_all"]:
        raise click.ClickException(
            "--update-all and --ignore(-core)-addons cannot be used together"
        )
    # Update Odoo datatabase
    try:
        _update_db(
            database,
            ctx.params["update_all"],
            ctx.params["i18n_overwrite"],
            watcher,
            ctx.params["list_only"],
            ignore_addons,
        )
    finally:
        if watcher:
            watcher.stop()
    # If we get here, the database has been updated
    with OdooEnvironment(database) as env:
        yield env


@click.command()
@click_odoo.env_options(
    with_rollback=False,
    database_must_exist=False,
    with_addons_path=True,
    environment_manager=OdooEnvironmentWithUpdate,
)
@click.option("--i18n-overwrite", is_flag=True, help="Overwrite existing translations")
@click.option("--update-all", is_flag=True, help="Force a complete upgrade (-u base)")
@click.option(
    "--ignore-addons",
    help=(
        "A comma-separated list of addons to ignore. "
        "These will not be updated if their checksum has changed. "
        "Use with care."
    ),
)
@click.option(
    "--ignore-core-addons",
    is_flag=True,
    help=(
        "If this option is set, Odoo CE and EE addons are not updated. "
        "This is normally safe, due the Odoo stable policy."
    ),
)
@click.option(
    "--if-exists", is_flag=True, help="Don't report error if database doesn't exist"
)
@click.option(
    "--watcher-max-seconds",
    default=0,
    type=float,
    help=(
        "Max DB lock seconds allowed before aborting the update process. "
        "Default: 0 (disabled)."
    ),
)
@click.option(
    "--list-only",
    is_flag=True,
    help="Log the list of addons to update without actually updating them.",
)
def main(
    env,
    i18n_overwrite,
    update_all,
    if_exists,
    watcher_max_seconds,
    list_only,
    ignore_addons,
    ignore_core_addons,
):
    """Update an Odoo database (odoo -u), automatically detecting
    addons to update based on a hash of their file content, compared
    to the hashes stored in the database.

    If you want to update in parallel while another Odoo instance is still
    running against the same database, you can use `--watcher-max-seconds`
    to start a watcher thread that aborts the update in case a DB
    lock is found. You will probably need to have at least 2 odoo codebases
    running in parallel (the old one, serving; the new one, updating) and
    swap them ASAP once the update is done. This process will reduce downtime
    a lot, but it requires deeper knowledge of Odoo internals to be used
    safely, so use it at your own risk.
    """
    if not env:
        msg = "Database does not exist"
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    # TODO: warn if modules to upgrade ?


if __name__ == "__main__":  # pragma: no cover
    main()
