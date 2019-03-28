#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import os
import shutil
import tempfile

import click
import click_odoo
from click_odoo import odoo

from ._backup import backup
from ._dbutils import db_exists, db_management_enabled


def _dump_db(dbname, backup):
    cmd = ["pg_dump", "--no-owner", dbname]
    filename = "dump.sql"
    if backup.format == "folder":
        cmd.insert(-1, "--format=c")
        filename = "db.dump"
    _stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
    backup.write(stdout, filename)


def _create_manifest(cr, dbname, backup):
    manifest = odoo.service.db.dump_db_manifest(cr)
    with tempfile.NamedTemporaryFile(mode="w") as f:
        json.dump(manifest, f, indent=4)
        f.seek(0)
        backup.addfile(f.name, "manifest.json")


def _backup_filestore(dbname, backup):
    filestore_source = odoo.tools.config.filestore(dbname)
    if os.path.isdir(filestore_source):
        backup.addtree(filestore_source, "filestore")


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
@click.option(
    "--force",
    is_flag=True,
    show_default=True,
    help="Don't report error if destination file/folder already exists.",
)
@click.option(
    "--if-exists", is_flag=True, help="Don't report error if database does not exist."
)
@click.option(
    "--format",
    type=click.Choice(["zip", "folder"]),
    default="zip",
    show_default=True,
    help="Output format",
)
@click.option(
    "--filestore/--no-filestore",
    default=True,
    show_default=True,
    help="Include filestore in backup",
)
@click.argument("dbname", nargs=1)
@click.argument("dest", nargs=1, required=1)
def main(env, dbname, dest, force, if_exists, format, filestore):
    """ Create an Odoo database backup from an existing one.

    This script dumps the database using pg_dump.
    It also copies the filestore.

    Unlike Odoo, this script allows you to make a backup of a
    database without going through the web interface. This
    avoids timeout and file size limitation problems when
    databases are too large.

    It also allows you to make a backup directly to a directory.
    This type of backup has the advantage that it reduces
    memory consumption since the files in the filestore are
    directly copied to the target directory as well as the
    database dump.

    """
    if not db_exists(dbname):
        msg = "Database does not exist: {}".format(dbname)
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    if os.path.exists(dest):
        msg = "Destination already exist: {}".format(dest)
        if not force:
            raise click.ClickException(msg)
        else:
            msg = "\n".join([msg, "Remove {}".format(dest)])
            click.echo(click.style(msg, fg="yellow"))
            if os.path.isfile(dest):
                os.unlink(dest)
            else:
                shutil.rmtree(dest)
    db = odoo.sql_db.db_connect(dbname)
    try:
        with backup(
            format, dest, "w"
        ) as _backup, db.cursor() as cr, db_management_enabled():
            _create_manifest(cr, dbname, _backup)
            if filestore:
                _backup_filestore(dbname, _backup)
            _dump_db(dbname, _backup)
    finally:
        odoo.sql_db.close_db(dbname)


if __name__ == "__main__":  # pragma: no cover
    main()
