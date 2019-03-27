# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess
import sys
import textwrap
import zipfile
from filecmp import dircmp

import pytest
from click.testing import CliRunner
from click_odoo import odoo

from click_odoo_contrib._dbutils import db_exists
from click_odoo_contrib.backupdb import main

TEST_DBNAME = "click-odoo-contrib-testbackupdb"
TEST_FILESTORE_FILE = "/dir1/f.txt"


def _dropdb(dbname):
    subprocess.check_call(["dropdb", "--if-exists", dbname])


def _dropdb_odoo(dbname):
    _dropdb(dbname)
    filestore_dir = odoo.tools.config.filestore(dbname)
    if os.path.isdir(filestore_dir):
        shutil.rmtree(filestore_dir)


def _createdb(dbname):
    subprocess.check_call(["createdb", dbname])


@pytest.fixture
def filestore():
    filestore_dir = odoo.tools.config.filestore(TEST_DBNAME)
    os.makedirs(filestore_dir)
    filstore_file = os.path.join(filestore_dir, *TEST_FILESTORE_FILE.split("/"))
    os.makedirs(os.path.dirname(filstore_file))
    with open(filstore_file, "w") as f:
        f.write("Hello world")
    try:
        yield
    finally:
        shutil.rmtree(filestore_dir)


@pytest.fixture
def pgdb():
    _createdb(TEST_DBNAME)
    try:
        yield TEST_DBNAME
    finally:
        _dropdb(TEST_DBNAME)


@pytest.fixture
def manifest():
    _original_f = odoo.service.db.dump_db_manifest
    try:
        odoo.service.db.dump_db_manifest = lambda a: {"manifest": "backupdb"}
        yield
    finally:
        odoo.service.db.dump_db_manifest = _original_f


def _check_backup(backup_dir, with_filestore=True):
    assert os.path.exists(os.path.join(backup_dir, "dump.sql")) or os.path.exists(
        os.path.join(backup_dir, "db.dump")
    )
    filestore_path = os.path.join(
        backup_dir, "filestore", *TEST_FILESTORE_FILE.split("/")[1:]
    )
    if with_filestore:
        assert os.path.exists(filestore_path)
    else:
        assert not os.path.exists(filestore_path)
    assert os.path.exists(os.path.join(backup_dir, "manifest.json"))


def _compare_filestore(dbname1, dbname2):
    filestore_dir_1 = odoo.tools.config.filestore(dbname1)
    filestore_dir_2 = odoo.tools.config.filestore(dbname2)
    if not os.path.exists(filestore_dir_1):
        # Odoo 8 wihout filestore
        assert not os.path.exists(filestore_dir_2)
        return
    diff = dircmp(filestore_dir_1, filestore_dir_2)
    assert not diff.left_only
    assert not diff.right_only
    assert not diff.diff_files


def tests_backupdb_zip(pgdb, filestore, tmp_path, manifest):
    zip_path = tmp_path.joinpath("test.zip")
    assert not zip_path.exists()
    zip_filename = zip_path.as_posix()
    result = CliRunner().invoke(main, ["--format=zip", TEST_DBNAME, zip_filename])
    assert result.exit_code == 0
    assert zip_path.exists()
    extract_dir = tmp_path.joinpath("extract_dir").as_posix()
    with zipfile.ZipFile(zip_filename) as zfile:
        zfile.extractall(extract_dir)
    _check_backup(extract_dir)


def tests_backupdb_zip_no_filestore(pgdb, filestore, tmp_path, manifest):
    zip_path = tmp_path.joinpath("test.zip")
    assert not zip_path.exists()
    zip_filename = zip_path.as_posix()
    result = CliRunner().invoke(
        main, ["--format=zip", "--no-filestore", TEST_DBNAME, zip_filename]
    )
    assert result.exit_code == 0
    assert zip_path.exists()
    extract_dir = tmp_path.joinpath("extract_dir").as_posix()
    with zipfile.ZipFile(zip_filename) as zfile:
        zfile.extractall(extract_dir)
    _check_backup(extract_dir, with_filestore=False)


def tests_backupdb_folder(pgdb, filestore, tmp_path, manifest):
    backup_path = tmp_path.joinpath("backup2")
    assert not backup_path.exists()
    backup_dir = backup_path.as_posix()
    result = CliRunner().invoke(main, ["--format=folder", TEST_DBNAME, backup_dir])
    assert result.exit_code == 0
    assert backup_path.exists()
    _check_backup(backup_dir)


def tests_backupdb_folder_no_filestore(pgdb, filestore, tmp_path, manifest):
    backup_path = tmp_path.joinpath("backup2")
    assert not backup_path.exists()
    backup_dir = backup_path.as_posix()
    result = CliRunner().invoke(
        main, ["--format=folder", "--no-filestore", TEST_DBNAME, backup_dir]
    )
    assert result.exit_code == 0
    assert backup_path.exists()
    _check_backup(backup_dir, with_filestore=False)


def tests_backupdb_no_list_db(odoodb, filestore, tmp_path):
    """backupdb should work even if list_db is set to False into odoo.cfg
    """
    zip_path = tmp_path.joinpath("test.zip")
    assert not zip_path.exists()
    zip_filename = zip_path.as_posix()
    odoo_cfg = tmp_path / "odoo.cfg"
    odoo_cfg.write_text(
        textwrap.dedent(
            u"""\
        [options]
        list_db = False
    """
        )
    )
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.backupdb",
        "-c",
        str(odoo_cfg),
        odoodb,
        zip_filename,
    ]
    subprocess.check_call(cmd)
    assert zip_path.exists()


def tests_backupdb_not_exists():
    assert not db_exists(TEST_DBNAME)
    result = CliRunner().invoke(main, [TEST_DBNAME, "out"])
    assert result.exit_code != 0
    assert "Database does not exist" in result.output
    result = CliRunner().invoke(main, ["--if-exists", TEST_DBNAME, "out"])
    assert result.exit_code == 0
    assert "Database does not exist" in result.output


def tests_backupdb_force_folder(pgdb, filestore, tmp_path, manifest):
    backup_dir = tmp_path.as_posix()
    result = CliRunner().invoke(main, ["--format=folder", TEST_DBNAME, backup_dir])
    assert result.exit_code != 0
    assert "Destination already exist" in result.output
    result = CliRunner().invoke(
        main, ["--format=folder", "--force", TEST_DBNAME, backup_dir]
    )
    assert result.exit_code == 0
    assert "Destination already exist" in result.output


def tests_backupdb_force_zip(pgdb, filestore, tmp_path, manifest):
    zip_path = tmp_path.joinpath("test.zip")
    zip_path.write_text(u"empty")
    zip_filename = zip_path.as_posix()
    result = CliRunner().invoke(main, ["--format=zip", TEST_DBNAME, zip_filename])
    assert result.exit_code != 0
    assert "Destination already exist" in result.output
    result = CliRunner().invoke(
        main, ["--format=zip", "--force", TEST_DBNAME, zip_filename]
    )
    assert result.exit_code == 0
    assert "Destination already exist" in result.output


def tests_backupdb_zip_restore(odoodb, odoocfg, tmp_path):
    """Test zip backup compatibility with native Odoo restore API
    """
    zip_path = tmp_path.joinpath("test.zip")
    zip_filename = zip_path.as_posix()
    result = CliRunner().invoke(main, ["--format=zip", odoodb, zip_filename])
    assert result.exit_code == 0
    assert zip_path.exists()
    try:
        assert not db_exists(TEST_DBNAME)
        with odoo.api.Environment.manage():
            odoo.service.db.restore_db(TEST_DBNAME, zip_filename, copy=True)
            odoo.sql_db.close_db(TEST_DBNAME)
        assert db_exists(TEST_DBNAME)
        _compare_filestore(odoodb, TEST_DBNAME)
    finally:
        _dropdb_odoo(TEST_DBNAME)


def tests_backupdb_folder_restore(odoodb, odoocfg, tmp_path):
    """Test the compatibility of the db dump file of a folder backup
    with native Odoo restore API
    """
    backup_path = tmp_path.joinpath("backup")
    assert not backup_path.exists()
    backup_dir = backup_path.as_posix()
    result = CliRunner().invoke(main, ["--format=folder", odoodb, backup_dir])
    assert result.exit_code == 0
    assert backup_path.exists()
    try:
        assert not db_exists(TEST_DBNAME)
        dumpfile = os.path.join(backup_dir, "db.dump")
        with odoo.api.Environment.manage():
            odoo.service.db.restore_db(TEST_DBNAME, dumpfile, copy=True)
            odoo.sql_db.close_db(TEST_DBNAME)
        assert db_exists(TEST_DBNAME)
    finally:
        _dropdb_odoo(TEST_DBNAME)
