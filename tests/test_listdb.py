# Copyright 2023 Moduon (https://www.moduon.team/)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import subprocess

import pytest
from click.testing import CliRunner

from click_odoo import odoo

from click_odoo_contrib.listdb import main


@pytest.fixture
def db_list_disabled():
    """Simulate an Odoo server started with --no-database-list."""
    old = odoo.tools.config["list_db"]
    odoo.tools.config["list_db"] = False
    yield
    odoo.tools.config["list_db"] = old


def test_listdb(odoodb):
    """Test that it only lists odoo-ready databases."""
    try:
        subprocess.check_call(["createdb", f"{odoodb}-not-odoo"])
        result = CliRunner().invoke(main)
        assert result.stdout.strip() == odoodb
    finally:
        subprocess.check_call(["dropdb", f"{odoodb}-not-odoo"])


def test_listdb_no_database_list(odoodb, db_list_disabled):
    """Test that it lists databases even with --no-database-list."""
    result = CliRunner().invoke(main)
    assert result.stdout.strip() == odoodb
