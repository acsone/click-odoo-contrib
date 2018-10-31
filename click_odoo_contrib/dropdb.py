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

from ._dbutils import db_exists, pg_connect


def _drop_db(cr, dbname):
    cr.execute("DROP DATABASE %s", (AsIs(quote_ident(dbname, cr)),))


def _drop_filestore(dbname):
    filestore_dir = odoo.tools.config.filestore(dbname)
    if os.path.exists(filestore_dir):
        shutil.rmtree(filestore_dir)


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
@click.option(
    "--if-exists", is_flag=True, help="Don't report error if database doesn't exist."
)
@click.argument("dbname", nargs=1)
def main(env, dbname, if_exists=False):
    """ Drop an Odoo database and associated file store. """
    if not db_exists(dbname):
        msg = "Database does not exist: {}".format(dbname)
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    with pg_connect() as cr:
        _drop_db(cr, dbname)
    _drop_filestore(dbname)
