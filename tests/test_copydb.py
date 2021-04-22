# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess
from collections import defaultdict

import pytest
from click.testing import CliRunner
from click_odoo import OdooEnvironment, odoo

from click_odoo_contrib._dbutils import db_exists
from click_odoo_contrib.copydb import main

TEST_DBNAME = "click-odoo-contrib-testcopydb"
TEST_DBNAME_NEW = "click-odoo-contrib-testcopydb-new"

ENTERPRISE_IR_CONGIG_KEYS = [
    "database.enterprise_code",
    "database.expiration_reason",
    "database.expiration_date",
]


def _dropdb(dbname):
    subprocess.check_call(["dropdb", "--if-exists", dbname])


def _createdb(dbname):
    subprocess.check_call(["createdb", dbname])


def _get_reset_config_params_key():
    major = odoo.release.version_info[0]
    default = ["database.uuid", "database.create_date", "web.base.url"]
    default = default + ENTERPRISE_IR_CONGIG_KEYS
    if major >= 9:
        default.append("database.secret")
    if major >= 12:
        default.extend(["base.login_cooldown_after", "base.login_cooldown_duration"])
    return default


def _assert_ir_config_reset(db1, db2):
    params_by_db = defaultdict(dict)
    for db in (db1, db2):
        with OdooEnvironment(database=db) as env:
            IrConfigParameters = env["ir.config_parameter"]
            for key in _get_reset_config_params_key():
                params_by_db[db][key] = IrConfigParameters.get_param(key)
    params1 = params_by_db[db1]
    params2 = params_by_db[db2]
    assert set(params1.keys()) == set(params2.keys())
    for k, v in params1.items():
        assert v != params2[k]


def _has_rsync():
    try:
        subprocess.check_call(["which", "rsync"])
        return True
    except subprocess.CalledProcessError as e:
        print(e)
        return False


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


@pytest.fixture
def ir_config_param_test_values(odoodb):
    with OdooEnvironment(database=odoodb) as env:
        for key in _get_reset_config_params_key():
            env.cr.execute(
                """
            UPDATE
                ir_config_parameter
            SET
                value='test value'
            WHERE
                key=%s
            RETURNING id
            """,
                (key,),
            )
            if not env.cr.fetchall():
                # Config parameter doesn't exist: create (ex enterprise params)
                env.cr.execute(
                    """
                INSERT INTO
                    ir_config_parameter
                    (key, value)
                VALUES
                    (%s, 'test value')
                """,
                    (key,),
                )


def tests_copydb(odoodb, ir_config_param_test_values):
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if not os.path.exists(filestore_dir_original):
        os.makedirs(filestore_dir_original)
    try:
        assert not db_exists(TEST_DBNAME_NEW)
        assert not os.path.exists(filestore_dir_new)
        result = CliRunner().invoke(
            main, ["--force-disconnect", odoodb, TEST_DBNAME_NEW]
        )
        assert result.exit_code == 0
        # this assert will indirectly test that the new db exists
        _assert_ir_config_reset(odoodb, TEST_DBNAME_NEW)
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


def test_copydb_no_source_filestore(odoodb, ir_config_param_test_values):
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if os.path.exists(filestore_dir_original):
        shutil.rmtree(filestore_dir_original)
    try:
        result = CliRunner().invoke(
            main, ["--force-disconnect", odoodb, TEST_DBNAME_NEW]
        )
        assert result.exit_code == 0
        # this assert will indirectly test that the new db exists
        _assert_ir_config_reset(odoodb, TEST_DBNAME_NEW)
        assert not os.path.isdir(filestore_dir_new)
    finally:
        _dropdb(TEST_DBNAME_NEW)


@pytest.mark.skipif(not _has_rsync(), reason="Cannot find `rsync` on test system")
def test_copydb_rsync(odoodb):
    # given an db with an existing filestore directory
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if not os.path.exists(filestore_dir_original):
        os.makedirs(filestore_dir_original)
    try:
        # when running copydb with mode rsync
        result = CliRunner().invoke(
            main, ["--filestore-copy-mode=rsync", odoodb, TEST_DBNAME_NEW]
        )

        # then the sync should be successful
        assert result.exit_code == 0
        # and the new db should exist
        _assert_ir_config_reset(odoodb, TEST_DBNAME_NEW)
        # and the filestore directory for the copied db should have been created
        assert os.path.isdir(filestore_dir_new)
    finally:
        # cleanup: drop copied db and created filestore dir
        _dropdb(TEST_DBNAME_NEW)
        if os.path.isdir(filestore_dir_new):
            shutil.rmtree(filestore_dir_new)


@pytest.mark.skipif(not _has_rsync(), reason="Cannot find `rsync` on test system")
def test_copydb_rsync_preexisting_filestore_dir(odoodb):
    # given an db with an existing filestore directory
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if not os.path.exists(filestore_dir_original):
        os.makedirs(filestore_dir_original)
    # and an existing target filestore
    if not os.path.exists(filestore_dir_new):
        os.makedirs(filestore_dir_new)
    try:
        # when running copydb with mode rsync
        result = CliRunner().invoke(
            main, ["--filestore-copy-mode=rsync", odoodb, TEST_DBNAME_NEW]
        )

        # then the sync should be successful
        assert result.exit_code == 0
        # and the new db should exist
        _assert_ir_config_reset(odoodb, TEST_DBNAME_NEW)
        # and the filestore directory for the copied db should have been created
        assert os.path.isdir(filestore_dir_new)
    finally:
        # cleanup: drop copied db and created filestore dir
        _dropdb(TEST_DBNAME_NEW)
        if os.path.isdir(filestore_dir_new):
            shutil.rmtree(filestore_dir_new)


@pytest.mark.skipif(not _has_rsync(), reason="Cannot find `rsync` on test system")
def test_copydb_rsync_hardlinks(odoodb):
    # given an db with an existing filestore directory
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if not os.path.exists(filestore_dir_original):
        os.makedirs(filestore_dir_original)
    try:
        # when running copydb with mode rsync
        result = CliRunner().invoke(
            main, ["--filestore-copy-mode=hardlink", odoodb, TEST_DBNAME_NEW]
        )

        # then the sync should be successful
        assert result.exit_code == 0
        # and the new db should exist
        _assert_ir_config_reset(odoodb, TEST_DBNAME_NEW)
        # and the filestore directory for the copied db should have been created
        assert os.path.isdir(filestore_dir_new)
    finally:
        # cleanup: drop copied db and created filestore dir
        _dropdb(TEST_DBNAME_NEW)
        if os.path.isdir(filestore_dir_new):
            shutil.rmtree(filestore_dir_new)


@pytest.mark.skipif(not _has_rsync(), reason="Cannot find `rsync` on test system")
def test_copydb_rsync_error(odoodb):
    # given an db with an existing filestore directory
    filestore_dir_new = odoo.tools.config.filestore(TEST_DBNAME_NEW)
    filestore_dir_original = odoo.tools.config.filestore(odoodb)
    if not os.path.exists(filestore_dir_original):
        os.makedirs(filestore_dir_original)
    # and an existing target filestore
    if not os.path.exists(filestore_dir_new):
        os.makedirs(filestore_dir_new)
    # that cannot be read nor written
    os.chmod(filestore_dir_new, 0)

    try:
        # when running copydb with mode rsync
        result = CliRunner().invoke(
            main, ["--filestore-copy-mode=rsync", odoodb, TEST_DBNAME_NEW]
        )

        # then the sync should be erroneous
        assert result.exit_code != 0
        # and an error should be given for the filestore
        assert "Error syncing filestore" in result.output
    finally:
        # cleanup: drop copied db and created filestore dir
        _dropdb(TEST_DBNAME_NEW)
        if os.path.isdir(filestore_dir_new):
            # make target dir writable again to be able to delete it
            os.chmod(filestore_dir_new, 0o700)
            shutil.rmtree(filestore_dir_new)
