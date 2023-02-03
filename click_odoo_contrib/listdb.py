#!/usr/bin/env python
# Copyright 2023 Moduon (https://www.moduon.team/)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
import click_odoo
from click_odoo import odoo

from ._dbutils import db_management_enabled


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False, with_rollback=False
)
def main(env):
    """List Odoo databases."""
    with db_management_enabled():
        all_dbs = odoo.service.db.list_dbs()
        bad_dbs = odoo.service.db.list_db_incompatible(all_dbs)
        good_dbs = set(all_dbs) - set(bad_dbs)
        for db in sorted(good_dbs):
            print(db)
    odoo.sql_db.close_all()


if __name__ == "__main__":  # pragma: no cover
    main()
