#!/usr/bin/env python
# Copyright 2023 Moduon (https://www.moduon.team/)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
import click_odoo
from click_odoo import odoo

from ._dbutils import db_management_enabled


@click.command()
@click.option(
    "--include-other-versions",
    is_flag=True,
    help="Include databases made by other Odoo versions.",
)
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
def main(env, include_other_versions):
    """List Odoo databases."""
    with db_management_enabled():
        all_dbs = odoo.service.db.list_dbs()
        if not include_other_versions:
            bad_dbs = odoo.service.db.list_db_incompatible(all_dbs)
            all_dbs = set(all_dbs) - set(bad_dbs)
        else:
            # Keep wrong-release dbs, but still skip non-Odoo ones.
            all_dbs = {
                db
                for db in all_dbs
                if odoo.tools.sql.table_exists(
                    odoo.sql_db.db_connect(db).cursor(), "ir_module_module"
                )
            }
        for db in sorted(all_dbs):
            print(db)
    odoo.sql_db.close_all()


if __name__ == "__main__":  # pragma: no cover
    main()
