#!/usr/bin/env python
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil

import click
import click_odoo
import psycopg2
from click_odoo import OdooEnvironment, odoo

from ._dbutils import db_exists, db_management_enabled, reset_config_parameters
from .backupdb import DBDUMP_FILENAME, FILESTORE_DIRNAME, MANIFEST_FILENAME


def _restore_from_folder(dbname, backup, copy=True, jobs=1, neutralize=False):
    manifest_file_path = os.path.join(backup, MANIFEST_FILENAME)
    dbdump_file_path = os.path.join(backup, DBDUMP_FILENAME)
    filestore_dir_path = os.path.join(backup, FILESTORE_DIRNAME)
    if not os.path.exists(manifest_file_path) or not os.path.exists(dbdump_file_path):
        msg = (
            "{} is not folder backup created by the backupdb command. "
            "{} and {} files are missing.".format(
                backup, MANIFEST_FILENAME, DBDUMP_FILENAME
            )
        )
        raise click.ClickException(msg)

    odoo.service.db._create_empty_database(dbname)
    pg_args = ["--jobs", str(jobs), "--dbname", dbname, "--no-owner", dbdump_file_path]
    if odoo.tools.exec_pg_command("pg_restore", *pg_args):
        raise click.ClickException("Couldn't restore database")
    if copy:
        # if it's a copy of a database, force generation of a new dbuuid
        reset_config_parameters(dbname)
    with OdooEnvironment(dbname) as env:
        if neutralize and odoo.release.version_info >= (16, 0):
            odoo.modules.neutralize.neutralize_database(env.cr)
        if os.path.exists(filestore_dir_path):
            filestore_dest = env["ir.attachment"]._filestore()
            shutil.move(filestore_dir_path, filestore_dest)

        if odoo.tools.config["unaccent"]:
            try:
                with env.cr.savepoint():
                    env.cr.execute("CREATE EXTENSION unaccent")
            except psycopg2.Error:
                pass
    odoo.sql_db.close_db(dbname)


def _restore_from_file(dbname, backup, copy=True, neutralize=False):
    with db_management_enabled():
        extra_kwargs = {}
        if odoo.release.version_info >= (16, 0):
            extra_kwargs["neutralize_database"] = neutralize
        odoo.service.db.restore_db(dbname, backup, copy, **extra_kwargs)
        odoo.sql_db.close_db(dbname)


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
@click.option(
    "--copy/--move",
    default=True,
    help=(
        "This database is a copy.\nIn order "
        "to avoid conflicts between databases, Odoo needs to know if this"
        "database was moved or copied. If you don't know, set is a copy."
    ),
)
@click.option(
    "--force",
    is_flag=True,
    show_default=True,
    help=(
        "Don't report error if destination database already exists. If "
        "force and destination database exists, it will be dropped before "
        "restore."
    ),
)
@click.option(
    "--neutralize",
    is_flag=True,
    show_default=True,
    help=(
        "Neutralize the database after restore. This will disable scheduled actions, "
        "outgoing emails, and sets other external providers in test mode. "
        "This works only in odoo 16.0 and above."
    ),
)
@click.option(
    "--jobs",
    help=(
        "Uses this many parallel jobs to restore. Only used to "
        "restore folder format backup."
    ),
    type=int,
    default=1,
)
@click.argument("dbname", nargs=1)
@click.argument(
    "source",
    nargs=1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
)
def main(env, dbname, source, copy, force, neutralize, jobs):
    """Restore an Odoo database backup.

    This script allows you to restore databses created by using the Odoo
    web interface or the backupdb script. This
    avoids timeout and file size limitation problems when
    databases are too large.
    """
    if db_exists(dbname):
        msg = "Destination database already exists: {}".format(dbname)
        if not force:
            raise click.ClickException(msg)
        msg = "{}, dropping it as requested.".format(msg)
        click.echo(click.style(msg, fg="yellow"))
        with db_management_enabled():
            odoo.service.db.exp_drop(dbname)
    if neutralize and odoo.release.version_info < (16, 0):
        raise click.ClickException(
            "--neutralize option is only available in odoo 16.0 and above"
        )
    if os.path.isfile(source):
        _restore_from_file(dbname, source, copy, neutralize)
    else:
        _restore_from_folder(dbname, source, copy, jobs, neutralize)
