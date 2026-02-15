#!/usr/bin/env python
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import click
import click_odoo

from ._dbutils import get_dev_demo_dbname
from .dropdb import _drop_db
from .initdb import _init_db
from .manifest import find_addons_bidir


@click.command()
@click_odoo.env_options(
    default_log_level="warn",
    with_database=False,
    with_rollback=False,
    with_addons_path=True,
)
@click.option(
    "--dbname",
    "-d",
    required=False,
    help="Name of database to drop and to create",
)
@click.argument("modules", nargs=1, required=False, default="base")
def main(
    env,
    dbname,
    modules,
):
    if not dbname:
        dbname = get_dev_demo_dbname()
    if not dbname:
        raise click.ClickException("No dbname provided")
    if modules == ".":
        addons = find_addons_bidir(modules)
        modules = ",".join(addon[0] for addon in addons)

    _drop_db(env, dbname)
    _init_db(
        env,
        dbname,
        modules,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
