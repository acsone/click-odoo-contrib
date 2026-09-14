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


def _fake_other_version_db(odoodb):
    """Create a db that looks like an Odoo db of another major version."""
    db_name = f"{odoodb}-other-version"
    subprocess.check_call(["createdb", db_name])
    subprocess.check_call(
        [
            "psql",
            "-q",
            "-d",
            db_name,
            "-c",
            "CREATE TABLE ir_module_module (name VARCHAR, latest_version VARCHAR)",
            "-c",
            "INSERT INTO ir_module_module (name, latest_version) "
            "VALUES ('base', '1.0')",
        ],
    )
    return db_name


def test_listdb_include_other_versions(odoodb):
    """Test that --include-other-versions lists other-version dbs too."""
    db_name = _fake_other_version_db(odoodb)
    try:
        result = CliRunner().invoke(main, ["--include-other-versions"])
        assert result.stdout.strip() == f"{odoodb}\n{db_name}"
    finally:
        subprocess.check_call(["dropdb", db_name])
