#!/usr/bin/env python
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import logging
import os
from contextlib import contextmanager

import click
import click_odoo
from click_odoo import OdooEnvironment, odoo

from ._addon_hash import addon_hash

_logger = logging.getLogger(__name__)


PARAM_INSTALLED_CHECKSUMS = "module_auto_update.installed_checksums"
PARAM_EXCLUDE_PATTERNS = "module_auto_update.exclude_patterns"
DEFAULT_EXCLUDE_PATTERNS = "*.pyc,*.pyo,i18n/*.pot,i18n_extra/*.pot,static/*"


def _get_param(cr, key, default=None):
    cr.execute("SELECT value FROM ir_config_parameter WHERE key=%s", (key,))
    r = cr.fetchone()
    if r:
        return r[0]
    else:
        return default


def _set_param(cr, key, value):
    cr.execute("UPDATE ir_config_parameter SET value=%s WHERE key=%s", (value, key))
    if not cr.rowcount:
        cr.execute(
            "INSERT INTO ir_config_parameter (key, value) VALUES (%s, %s)", (key, value)
        )


def _load_installed_checksums(cr):
    value = _get_param(cr, PARAM_INSTALLED_CHECKSUMS)
    if value:
        return json.loads(value)
    else:
        return {}


def _save_installed_checksums(cr):
    checksums = {}
    cr.execute("SELECT name FROM ir_module_module WHERE state='installed'")
    for (module_name,) in cr.fetchall():
        checksums[module_name] = _get_checksum_dir(cr, module_name)
    _set_param(cr, PARAM_INSTALLED_CHECKSUMS, json.dumps(checksums))


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


@contextmanager
def OdooEnvironmentWithUpdate(database, ctx, **kwargs):
    conn = odoo.sql_db.db_connect(database)
    to_update = odoo.tools.config["update"]
    if ctx.params["update_all"]:
        to_update["base"] = 1
    else:
        with conn.cursor() as cr:
            checksums = _load_installed_checksums(cr)
            cr.execute("SELECT name FROM ir_module_module WHERE state = 'installed'")
            for (module_name,) in cr.fetchall():
                if _get_checksum_dir(cr, module_name) != checksums.get(module_name):
                    to_update[module_name] = 1
        if to_update:
            _logger.info(
                "Updating addons for their hash changed: %s.",
                ",".join(to_update.keys()),
            )
    if ctx.params["i18n_overwrite"]:
        odoo.tools.config["overwrite_existing_translations"] = True
    if odoo.release.version_info[0] < 10:
        Registry = odoo.modules.registry.RegistryManager
    else:
        Registry = odoo.modules.registry.Registry
    Registry.new(database, update_module=True)
    with conn.cursor() as cr:
        _save_installed_checksums(cr)
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
    "--if-exists", is_flag=True, help="Don't report error if database doesn't exist"
)
def main(env, i18n_overwrite, update_all, if_exists):
    """ Update an Odoo database (odoo -u), automatically detecting
    addons to update based on a hash of their file content, compared
    to the hashes stored in the database.
    """
    if not env:
        msg = "Database does not exist"
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    # TODO: warn/err if modules to upgrade


if __name__ == "__main__":  # pragma: no cover
    main()
