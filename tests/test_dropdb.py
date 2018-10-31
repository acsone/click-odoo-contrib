# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess

import pytest
from click.testing import CliRunner
from click_odoo import odoo

from click_odoo_contrib._dbutils import db_exists
from click_odoo_contrib.dropdb import main

TEST_DBNAME = "click-odoo-contrib-testdropdb"


def _dropdb(dbname):
    subprocess.check_call(["dropdb", "--if-exists", dbname])


@pytest.fixture
def filestore():
    filestore_dir = odoo.tools.config.filestore(TEST_DBNAME)
    os.makedirs(filestore_dir)
    try:
        yield
    finally:
        if os.path.exists(filestore_dir):
            shutil.rmtree(filestore_dir)


@pytest.fixture
def pgdb():
    subprocess.check_call(["createdb", TEST_DBNAME])
    try:
        yield TEST_DBNAME
    finally:
        _dropdb(TEST_DBNAME)


def tests_dropdb(pgdb, filestore):
    filestore_dir = odoo.tools.config.filestore(TEST_DBNAME)
    # sanity check for fixture
    assert os.path.isdir(filestore_dir)
    assert db_exists(TEST_DBNAME)
    # drop
    result = CliRunner().invoke(main, [TEST_DBNAME])
    assert result.exit_code == 0
    assert not os.path.exists(filestore_dir)
    assert not db_exists(TEST_DBNAME)


def tests_dropdb_not_exists():
    assert not db_exists(TEST_DBNAME)
    result = CliRunner().invoke(main, [TEST_DBNAME])
    assert result.exit_code != 0
    assert "Database does not exist" in result.output
    result = CliRunner().invoke(main, ["--if-exists", TEST_DBNAME])
    assert result.exit_code == 0
    assert "Database does not exist" in result.output
