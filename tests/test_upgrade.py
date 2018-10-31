# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from click.testing import CliRunner

from click_odoo_contrib.upgrade import main


def test_upgrade_db_not_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["-d", "dbthatdoesnotexist"])
    assert result.exit_code != 0
    runner = CliRunner()
    result = runner.invoke(main, ["--if-exists", "-d", "dbthatdoesnotexist"])
    assert result.exit_code == 0
