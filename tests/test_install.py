# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from click.testing import CliRunner
from click_odoo import OdooEnvironment

from click_odoo_contrib.install import main


def test_install(odoodb):
    with OdooEnvironment(database=odoodb) as env:
        Imm = env["ir.module.module"]
        assert Imm.search([("name", "=", "product"), ("state", "=", "uninstalled")])
    result = CliRunner().invoke(main, ["-d", odoodb, "-m", "product"])
    assert result.exit_code == 0
    with OdooEnvironment(database=odoodb) as env:
        Imm = env["ir.module.module"]
        assert Imm.search([("name", "=", "product"), ("state", "=", "installed")])
