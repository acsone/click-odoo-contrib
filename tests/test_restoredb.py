# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import operator
import os
import shutil
import subprocess
from collections import defaultdict

import click_odoo
import pytest
from click.testing import CliRunner
from click_odoo import odoo

from click_odoo_contrib._dbutils import db_exists
from click_odoo_contrib.backupdb import main as backupdb
from click_odoo_contrib.restoredb import main as restoredb

TEST_DBNAME = "click-odoo-contrib-testrestoredb"

_DEFAULT_IR_CONFIG_PARAMETERS = ["database.uuid", "database.create_date"]


def _createdb(dbname):
    subprocess.check_call(["createdb", dbname])


def _dropdb(dbname):
    odoo.sql_db.close_all()
    subprocess.check_call(["dropdb", "--if-exists", dbname])


def _dropdb_odoo(dbname):
    _dropdb(dbname)
    filestore_dir = odoo.tools.config.filestore(dbname)
    if os.path.isdir(filestore_dir):
        shutil.rmtree(filestore_dir)


def _check_default_params(db1, db2, operator):
    params_by_db = defaultdict(dict)
    for db in (db1, db2):
        with click_odoo.OdooEnvironment(database=db) as env:
            IrConfigParameters = env["ir.config_parameter"]
            for key in _DEFAULT_IR_CONFIG_PARAMETERS:
                params_by_db[db][key] = IrConfigParameters.get_param(key)
    params1 = params_by_db[db1]
    params2 = params_by_db[db2]
    assert set(params1.keys()) == set(params2.keys())
    for k, v in params1.items():
        assert operator(v, params2[k])


@pytest.fixture(params=["folder", "zip", "dump"])
def backup(request, odoodb, odoocfg, tmp_path):
    if request.param == "folder":
        name = "backup"
    elif request.param == "zip":
        name = "backup.zip"
    else:
        name = "backup.dump"
    path = tmp_path.joinpath(name)
    posix_path = path.as_posix()
    CliRunner().invoke(
        backupdb, ["--format={}".format(request.param), odoodb, posix_path]
    )
    yield posix_path, odoodb


def test_db_restore(backup):
    assert not db_exists(TEST_DBNAME)
    backup_path, original_db = backup
    try:
        result = CliRunner().invoke(restoredb, [TEST_DBNAME, backup_path])
        assert result.exit_code == 0
        assert db_exists(TEST_DBNAME)
        # default restore mode is copy -> default params are not preserved
        _check_default_params(TEST_DBNAME, original_db, operator.ne)
    finally:
        _dropdb_odoo(TEST_DBNAME)


def test_db_restore_target_exists(backup):
    _createdb(TEST_DBNAME)
    backup_path, original_db = backup
    try:
        result = CliRunner().invoke(restoredb, [TEST_DBNAME, backup_path])
        assert result.exit_code != 0, result.output
        assert "Destination database already exists" in result.output
    finally:
        _dropdb_odoo(TEST_DBNAME)
    try:
        result = CliRunner().invoke(restoredb, ["--force", TEST_DBNAME, backup_path])
        assert result.exit_code == 0
        assert db_exists(TEST_DBNAME)
    finally:
        _dropdb_odoo(TEST_DBNAME)


def test_db_restore_move(backup):
    assert not db_exists(TEST_DBNAME)
    backup_path, original_db = backup
    try:
        result = CliRunner().invoke(restoredb, ["--move", TEST_DBNAME, backup_path])
        assert result.exit_code == 0
        assert db_exists(TEST_DBNAME)
        # when database is moved, default params are preserved
        _check_default_params(TEST_DBNAME, original_db, operator.eq)
    finally:
        _dropdb_odoo(TEST_DBNAME)


def test_db_restore_neutralize(backup):
    assert not db_exists(TEST_DBNAME)
    backup_path, _original_db = backup
    try:
        result = CliRunner().invoke(
            restoredb, ["--neutralize", TEST_DBNAME, backup_path]
        )
        if odoo.release.version_info < (16, 0):
            assert result.exit_code != 0, result.output
            assert (
                "--neutralize option is only available in odoo 16.0 and above"
                in result.output
            )
            assert not db_exists(TEST_DBNAME)
        else:
            assert result.exit_code == 0
            assert db_exists(TEST_DBNAME)
            with click_odoo.OdooEnvironment(database=TEST_DBNAME) as env:
                IrConfigParameters = env["ir.config_parameter"]
                assert IrConfigParameters.get_param("database.is_neutralized") == "true"
    finally:
        _dropdb_odoo(TEST_DBNAME)
