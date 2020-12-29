#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

import click
import click_odoo
from click_odoo import odoo

from ._dbutils import db_exists, db_management_enabled


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
    with db_management_enabled():
        # Work around odoo.service.db.list_dbs() not finding the database
        # when postgres connection info is passed as PG* environment
        # variables.
        if odoo.release.version_info < (12, 0):
            for v in ("host", "port", "user", "password"):
                odoov = "db_" + v.lower()
                pgv = "PG" + v.upper()
                if not odoo.tools.config[odoov] and pgv in os.environ:
                    odoo.tools.config[odoov] = os.environ[pgv]
        odoo.service.db.exp_drop(dbname)


if __name__ == "__main__":  # pragma: no cover
    main()
