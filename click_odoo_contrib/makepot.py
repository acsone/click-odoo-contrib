# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

import click
import click_odoo

from . import manifest
from . import gitutils


def export_pot(env, addon_name, addons_dir, commit):
    addon_dir = os.path.join(addons_dir, addon_name)
    pot_filename = os.path.join(addon_dir, addon_name + '.pot')
    # TODO
    gitutils.commit_if_needed(
        pot_filename,
        "[UPD] {}.pot".format(addon_name),
        cwd=addon_dir,
    )


@click.command()
@click_odoo.env_options(with_rollback=False, default_log_level='error')
@click.option('--addons-dir', default='.', show_default=True)
@click.option('--commit / --no-commit', show_default=True,
              help="Git commit exported .pot files if needed.")
def main(env, addons_dir, commit):
    """ Export translation (.pot) files of addons
    installed in the database and present in addons_dir.
    """
    addon_names = [
        addon_name
        for addon_name, _, _ in manifest.find_addons(addons_dir)
    ]
    if addon_names:
        modules = env['ir.module.module'].search([
            ('state', '=', 'installed'),
            ('name', 'in', addon_names),
        ])
        for module in modules:
            export_pot(env, module.name, addons_dir, commit)
