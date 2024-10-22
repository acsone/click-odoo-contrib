#!/usr/bin/env python
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import click
import click_odoo

from .update import _get_ignore_addons, _save_installed_checksums


@click.command()
@click_odoo.env_options()
@click.option(
    "--ignore-addons",
    help=(
        "A comma-separated list of addons to ignore. "
        "These will not be updated if their checksum has changed. "
        "Use with care."
    ),
)
@click.option(
    "--ignore-core-addons",
    is_flag=True,
    help=(
        "If this option is set, Odoo CE and EE addons are not updated. "
        "This is normally safe, due the Odoo stable policy."
    ),
)
def main(
    env,
    ignore_addons,
    ignore_core_addons,
):
    """Initialise Hash Values of installed Addons"""
    ignore_addons = _get_ignore_addons(ignore_addons, ignore_core_addons)
    _save_installed_checksums(env.cr, ignore_addons)


if __name__ == "__main__":  # pragma: no cover
    main()
