#!/usr/bin/env python
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

import click
import click_odoo

_logger = logging.getLogger(__name__)


def install(env, module_names):
    modules = env["ir.module.module"].search([("name", "in", module_names)])
    _logger.info("installing %s", modules.mapped("name"))
    modules.button_immediate_install()
    env.cr.commit()


@click.command()
@click_odoo.env_options(with_rollback=False)
@click.option(
    "--modules",
    "-m",
    required=True,
    help="Comma-separated list of modules to install",
)
def main(env, modules):
    module_names = [m.strip() for m in modules.split(",")]
    install(env, module_names)


if __name__ == "__main__":  # pragma: no cover
    main()
