#!/usr/bin/env python
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
import click_odoo
from click_odoo import odoo

from ._dbutils import db_exists, db_management_enabled, get_dev_demo_dbname


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
@click.option(
    "--if-exists", is_flag=True, help="Don't report error if database doesn't exist."
)
@click.argument("dbname", nargs=1, required=False)
def main(env, dbname=None, if_exists=False):
    """Drop an Odoo database and associated file store."""
    if not dbname:
        dbname = get_dev_demo_dbname()
    if not dbname:
        raise click.ClickException("No dbname provided")
    if not db_exists(dbname):
        msg = "Database does not exist: {}".format(dbname)
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    with db_management_enabled():
        odoo.service.db.exp_drop(dbname)


if __name__ == "__main__":  # pragma: no cover
    main()
