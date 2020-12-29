# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess
import sys

import pytest
from click_odoo import odoo

from click_odoo_contrib._dbutils import db_exists

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


def test_dropdb_exists(pgdb, filestore):
    filestore_dir = odoo.tools.config.filestore(TEST_DBNAME)
    # sanity check for fixture
    assert os.path.isdir(filestore_dir)
    assert db_exists(TEST_DBNAME)
    # drop
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "click_odoo_contrib.dropdb",
            "--if-exists",
            "--log-level=debug_sql",
            TEST_DBNAME,
        ],
        universal_newlines=True,
    )
    assert not os.path.exists(filestore_dir), filestore_dir
    assert not db_exists(TEST_DBNAME)


def test_dropdb_not_exists():
    assert not db_exists(TEST_DBNAME)
    with pytest.raises(subprocess.CalledProcessError) as e:
        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "click_odoo_contrib.dropdb",
                TEST_DBNAME,
            ],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        )
    assert "Database does not exist" in e.value.output
    output = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "click_odoo_contrib.dropdb",
            "--if-exists",
            TEST_DBNAME,
        ],
        universal_newlines=True,
        stderr=subprocess.STDOUT,
    )
    assert "Database does not exist" in output
