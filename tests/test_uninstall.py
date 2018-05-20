# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from click.testing import CliRunner

from click_odoo import odoo, OdooEnvironment

from click_odoo_contrib.uninstall import main

# This hack is necessary because the way CliRunner patches
# stdout is not compatible with the Odoo logging initialization
# mechanism. Logging is therefore tested with subprocesses.
odoo.netsvc._logger_init = True


def test_uninstall(odoodb):
    with OdooEnvironment(database=odoodb) as env:
        Imm = env['ir.module.module']
        assert Imm.search([
            ('name', '=', 'base_import'),
            ('state', '=', 'installed'),
        ])
    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-m', 'base_import',
    ])
    assert result.exit_code == 0
    with OdooEnvironment(database=odoodb) as env:
        Imm = env['ir.module.module']
        assert not Imm.search([
            ('name', '=', 'base_import'),
            ('state', '=', 'installed'),
        ])
