#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil

import click
import click_odoo
from click_odoo import odoo
from psycopg2.extensions import AsIs, quote_ident

from ._dbutils import (
    db_exists,
    pg_connect,
    reset_config_parameters,
    terminate_connections,
)


def _copy_db(cr, source, dest):
    cr.execute(
        "CREATE DATABASE %s WITH TEMPLATE %s",
        (AsIs(quote_ident(dest, cr)), AsIs(quote_ident(source, cr))),
    )


def _copy_filestore(source, dest, diff=False):
    filestore_source = odoo.tools.config.filestore(source)
    if os.path.isdir(filestore_source):
        filestore_dest = odoo.tools.config.filestore(dest)
        if diff:

            def _ignore_existing(directory, children):
                paths = {
                    child: {
                        "old": os.path.join(directory, child),
                        "new": os.path.join(
                            filestore_dest,
                            os.path.relpath(
                                os.path.join(directory, child), filestore_source
                            ),
                        ),
                    }
                    for child in children
                }
                return [
                    child
                    for child in paths
                    if not os.path.isdir(
                        paths[child]["old"]
                    )  # do not ignore directories
                    and os.path.exists(paths[child]["new"])  # ignore existing files
                ]

            shutil.copytree(
                filestore_source,
                filestore_dest,
                ignore=_ignore_existing,
                dirs_exist_ok=True,
            )
        else:
            shutil.copytree(filestore_source, filestore_dest)


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
@click.option(
    "--force-disconnect",
    "-f",
    is_flag=True,
    help="Attempt to disconnect users from the template database.",
)
@click.option(
    "--unless-dest-exists",
    is_flag=True,
    help="Don't report error if destination database already exists.",
)
@click.option(
    "--if-source-exists",
    is_flag=True,
    help="Don't report error if source database does not exist.",
)
@click.option(
    "--filestore-diff",
    is_flag=True,
    help="Only copy new files in filestore (needs python >= 3.8).",
)
@click.argument("source", required=True)
@click.argument("dest", required=True)
def main(
    env,
    source,
    dest,
    force_disconnect,
    unless_dest_exists,
    if_source_exists,
    filestore_diff,
):
    """Create an Odoo database by copying an existing one.

    This script copies using postgres CREATEDB WITH TEMPLATE.
    It also copies the filestore.
    """
    with pg_connect() as cr:
        if db_exists(dest):
            msg = "Destination database already exists: {}".format(dest)
            if unless_dest_exists:
                click.echo(click.style(msg, fg="yellow"))
                return
            else:
                raise click.ClickException(msg)
        if not db_exists(source):
            msg = "Source database does not exist: {}".format(source)
            if if_source_exists:
                click.echo(click.style(msg, fg="yellow"))
                return
            else:
                raise click.ClickException(msg)
        if force_disconnect:
            terminate_connections(source)
        _copy_db(cr, source, dest)
        reset_config_parameters(dest)
    _copy_filestore(source, dest, diff=filestore_diff)


if __name__ == "__main__":  # pragma: no cover
    main()
