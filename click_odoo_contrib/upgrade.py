#!/usr/bin/env python

import logging

import click
import click_odoo
from click_odoo import odoo

_logger = logging.getLogger(__name__)


def upgrade(env, i18n_overwrite=False, upgrade_all=False):
    Imm = env['ir.module.module']
    if hasattr(Imm, 'upgrade_changed_checksum') and not upgrade_all:
        Imm.upgrade_changed_checksum(
            overwrite_existing_translations=i18n_overwrite)
    else:
        if upgrade_all:
            _logger.info("complete upgrade forced, performing -u base")
        else:
            _logger.warning(
                "upgrade_changed_checksum not found, performing -u base")
        odoo.tools.config['overwrite_existing_translations'] = \
            i18n_overwrite
        Imm.update_list()
        Imm.search([('name', '=', 'base')]).button_upgrade()
        env.cr.commit()
        env['base.module.upgrade'].upgrade_module()
        env.cr.commit()
        # save installed checksums after regular upgrade
        if hasattr(Imm, '_save_installed_checksums'):
            Imm._save_installed_checksums()
            env.cr.commit()


@click.command()
@click_odoo.env_options(with_rollback=False)
@click.option('--i18n-overwrite', is_flag=True,
              help="Overwrite existing translations")
@click.option('--upgrade-all', is_flag=True,
              help="Force a complete upgrade (-u base)")
def main(env, i18n_overwrite, upgrade_all):
    upgrade(env, i18n_overwrite, upgrade_all)


if __name__ == '__main__':
    main()
