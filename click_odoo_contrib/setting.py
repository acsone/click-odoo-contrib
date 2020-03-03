#!/usr/bin/env python
# coding: utf-8
# © 2019 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import ast

import click
import click_odoo


@click.command()
@click_odoo.env_options(
    default_log_level="info", with_database=True, with_rollback=False
)
@click.argument("settings_file_name", type=click.Path(exists=True))
def main(env, settings_file_name):
    """ Use a dict of settings provided with a python file
        {
            ...
            'group_uom': True,
            ...
        }
        to apply on your odoo database
    """
    with open(settings_file_name, "r") as erp_settings:
        settings = {}
        settings = ast.literal_eval(erp_settings.read())
        settings_model = env["res.config.settings"]
        for cpny in env["res.company"].search([]):
            # We only need the last configuration record
            config = settings_model.search(
                [("company_id", "=", cpny.id)], limit=1, order="id desc"
            )
            if not config:
                # first configuration
                config = settings_model.create({"company_id": cpny.id})
            config.write(settings)
            # Execute the record in order to trigger save and to apply settings
            config.execute()


if __name__ == "__main__":  # pragma: no cover
    main()
