# Copyright 2023 Moduon (https://www.moduon.team/)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import subprocess

from click.testing import CliRunner

from click_odoo_contrib.listdb import main


def test_listdb(odoodb):
    """Test that it only lists odoo-ready databases."""
    try:
        subprocess.check_call(["createdb", f"{odoodb}-not-odoo"])
        result = CliRunner().invoke(main)
        assert result.stdout.strip() == odoodb
    finally:
        subprocess.check_call(["dropdb", f"{odoodb}-not-odoo"])
