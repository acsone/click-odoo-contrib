# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess

import pytest
from click.testing import CliRunner
from click_odoo import odoo

from click_odoo_contrib._dbutils import db_exists
from click_odoo_contrib.copydb import main

TEST_DBNAME = "click-odoo-contrib-testcopydb"
TEST_DBNAME_NEW = "click-odoo-contrib-testcopydb-new"


def _dropdb(dbname):
    subprocess.check_call(["dropdb", "--if-exists", dbname])


def _createdb(dbname):
    subprocess.check_call(["createdb", dbname])


@pytest.fixture
def filestore():
    filestore_dir = odoo.tools.config.filestore(TEST_DBNAME)
    os.makedirs(filestore_dir)
    try:
        yield
    finally:
        shutil.rmtree(filestore_dir)


@pytest.fixture
def pgdb():
    subprocess.check_call(["createdb", TEST_DBNAME])
    try:
        yield TEST_DBNAME
    finally:
        _dropdb(TEST_DBNAME)


def tests_copydb(pgdb, filestore):
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    try:
        assert not db_exists(TEST_DBNAME_NEW)
        assert not os.path.exists(filestore_dir_new)
        result = CliRunner().invoke(
            main, ["--force-disconnect", TEST_DBNAME, TEST_DBNAME_NEW]
        )
        assert result.exit_code == 0
        # this dropdb will indirectly test that the new db exists
        subprocess.check_call(["dropdb", TEST_DBNAME_NEW])
        assert os.path.isdir(filestore_dir_new)
    finally:
        _dropdb(TEST_DBNAME_NEW)
        if os.path.isdir(filestore_dir_new):
            shutil.rmtree(filestore_dir_new)


def tests_copydb_template_absent():
    assert not db_exists(TEST_DBNAME)
    assert not db_exists(TEST_DBNAME_NEW)
    result = CliRunner().invoke(main, [TEST_DBNAME, TEST_DBNAME_NEW])
    assert result.exit_code != 0
    assert "Source database does not exist" in result.output
    result = CliRunner().invoke(
        main, ["--if-source-exists", TEST_DBNAME, TEST_DBNAME_NEW]
    )
    assert result.exit_code == 0
    assert "Source database does not exist" in result.output


def test_copydb_target_exists(pgdb):
    _createdb(TEST_DBNAME_NEW)
    try:
        assert db_exists(TEST_DBNAME)
        assert db_exists(TEST_DBNAME_NEW)
        result = CliRunner().invoke(main, [TEST_DBNAME, TEST_DBNAME_NEW])
        assert result.exit_code != 0
        assert "Destination database already exists" in result.output
        result = CliRunner().invoke(
            main, ["--unless-dest-exists", TEST_DBNAME, TEST_DBNAME_NEW]
        )
        assert result.exit_code == 0
        assert "Destination database already exists" in result.output
    finally:
        _dropdb(TEST_DBNAME_NEW)


def test_copydb_template_not_exists_target_exists():
    _createdb(TEST_DBNAME_NEW)
    try:
        assert not db_exists(TEST_DBNAME)
        assert db_exists(TEST_DBNAME_NEW)
        result = CliRunner().invoke(
            main,
            [
                "--if-source-exists",
                "--unless-dest-exists",
                TEST_DBNAME,
                TEST_DBNAME_NEW,
            ],
        )
        assert result.exit_code == 0
    finally:
        _dropdb(TEST_DBNAME_NEW)


def test_copydb_no_source_filestore(pgdb):
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    try:
        result = CliRunner().invoke(
            main, ["--force-disconnect", TEST_DBNAME, TEST_DBNAME_NEW]
        )
        assert result.exit_code == 0
        # this dropdb will indirectly test that the new db exists
        subprocess.check_call(["dropdb", TEST_DBNAME_NEW])
        assert not os.path.isdir(filestore_dir_new)
    finally:
        _dropdb(TEST_DBNAME_NEW)
