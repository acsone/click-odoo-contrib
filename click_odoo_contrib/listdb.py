#!/usr/bin/env python
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
import click_odoo
from click_odoo import odoo

from ._dbutils import (
    db_management_enabled,
)


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=False,
)
def main(
    env,
):
    """List available Odoo databases.

    This script just lists the databases.
    """
    dbname = env.dbname
    with db_management_enabled():
        databases = odoo.service.db.list_dbs(True)
    # print the list
    for database in databases:
        msg = "{}{}".format(database, ' *' if database == dbname else '')
        click.echo(click.style(msg))


if __name__ == "__main__":  # pragma: no cover
    main()
