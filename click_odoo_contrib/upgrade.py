#!/usr/bin/env python
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

import click
import click_odoo
from click_odoo import odoo

_logger = logging.getLogger(__name__)


def ensure_module_state(env, modules, state):
    # read module states, bypassing any Odoo cache
    env.cr.execute(
        "SELECT name FROM ir_module_module " "WHERE id IN %s AND state != %s",
        (tuple(modules.ids), state),
    )
    names = [r[0] for r in env.cr.fetchall()]
    if names:
        raise click.ClickException(
            "The following modules should be in state '%s' "
            "at this stage: %s. Bailing out for safety." % (state, ",".join(names))
        )


def upgrade(env, i18n_overwrite=False, upgrade_all=False):
    Imm = env["ir.module.module"]
    if hasattr(Imm, "upgrade_changed_checksum") and not upgrade_all:
        Imm.upgrade_changed_checksum(overwrite_existing_translations=i18n_overwrite)
    else:
        if upgrade_all:
            _logger.info("complete upgrade forced, performing -u base")
        else:
            _logger.warning("upgrade_changed_checksum not found, performing -u base")
        odoo.tools.config["overwrite_existing_translations"] = i18n_overwrite
        Imm.update_list()
        modules_to_upgrade = Imm.search([("name", "=", "base")])
        modules_to_upgrade.button_upgrade()
        env.cr.commit()
        # in rare situations, button_upgrade may fail without
        # exception, this would lead to corruption because
        # no upgrade would be performed and save_installed_checksums
        # would update cheksums for modules that have not been upgraded
        ensure_module_state(env, modules_to_upgrade, "to upgrade")
        env["base.module.upgrade"].upgrade_module()
        env.cr.commit()
        # save installed checksums after regular upgrade
        if hasattr(Imm, "_save_installed_checksums"):
            Imm._save_installed_checksums()
            env.cr.commit()


@click.command()
@click_odoo.env_options(
    with_rollback=False, database_must_exist=False, with_addons_path=True
)
@click.option("--i18n-overwrite", is_flag=True, help="Overwrite existing translations")
@click.option("--upgrade-all", is_flag=True, help="Force a complete upgrade (-u base)")
@click.option(
    "--if-exists", is_flag=True, help="Don't report error if database doesn't exist"
)
def main(env, i18n_overwrite, upgrade_all, if_exists):
    """ Upgrade an Odoo database (odoo -u),
    taking advantage of module_auto_update's
    upgrade_changed_checksum method if present.
    """
    click.echo(
        click.style(
            "click-odoo-upgrade is deprecated, use click-odoo-update.", fg="red"
        )
    )
    if not env:
        msg = "Database does not exist"
        if if_exists:
            click.echo(click.style(msg, fg="yellow"))
            return
        else:
            raise click.ClickException(msg)
    upgrade(env, i18n_overwrite, upgrade_all)


if __name__ == "__main__":  # pragma: no cover
    main()
