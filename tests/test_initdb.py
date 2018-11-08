# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta

import click_odoo
import mock
import pytest
from click.testing import CliRunner

from click_odoo_contrib import initdb
from click_odoo_contrib.initdb import DbCache, main

TEST_DBNAME = "click-odoo-contrib-testinitdb"
TEST_DBNAME_NEW = "click-odoo-contrib-testinitdb-new"
TEST_PREFIX = "tstpfx9"
TEST_HASH1 = "a" * DbCache.HASH_SIZE
TEST_HASH2 = "b" * DbCache.HASH_SIZE
TEST_HASH3 = "c" * DbCache.HASH_SIZE
TODAY = datetime(2018, 5, 10)
TODAY_MINUS_2 = datetime(2018, 5, 8)
TODAY_MINUS_4 = datetime(2018, 5, 6)
ADDONS_PATH = ",".join(
    [
        os.path.join(click_odoo.odoo.__path__[0], "addons"),
        os.path.join(click_odoo.odoo.__path__[0], "..", "addons"),
        os.path.join(os.path.dirname(__file__), "data", "test_initdb"),
    ]
)


def _dropdb(dbname):
    subprocess.check_call(["dropdb", "--if-exists", dbname])


@pytest.fixture
def pgdb():
    subprocess.check_call(["createdb", TEST_DBNAME])
    try:
        yield TEST_DBNAME
    finally:
        _dropdb(TEST_DBNAME)


@pytest.fixture
def dbcache():
    with DbCache(TEST_PREFIX) as c:
        try:
            yield c
        finally:
            c.purge()


def test_dbcache_create(pgdb, dbcache):
    assert dbcache.size == 0
    assert not dbcache.create(TEST_DBNAME_NEW, TEST_HASH1)
    with mock.patch.object(initdb, "datetime") as mock_dt:
        # create a few db with known dates
        mock_dt.utcnow.return_value = TODAY_MINUS_4
        dbcache.add(pgdb, TEST_HASH1)
        assert dbcache.size == 1
        mock_dt.utcnow.return_value = TODAY
        assert dbcache.create(TEST_DBNAME_NEW, TEST_HASH1)
        try:
            assert dbcache.size == 1
            # ensure the cached template has been "touched"
            dbcache.trim_age(timedelta(days=3))
            assert dbcache.size == 1
        finally:
            _dropdb(TEST_DBNAME_NEW)
        # test recreate (same day)
        assert dbcache.create(TEST_DBNAME_NEW, TEST_HASH1)
        _dropdb(TEST_DBNAME_NEW)


def test_dbcache_purge(pgdb, dbcache):
    assert dbcache.size == 0
    dbcache.add(pgdb, TEST_HASH1)
    assert dbcache.size == 1
    dbcache.purge()
    assert dbcache.size == 0


def test_dbcache_trim_size(pgdb, dbcache):
    assert dbcache.size == 0
    dbcache.add(pgdb, TEST_HASH1)
    assert dbcache.size == 1
    dbcache.add(pgdb, TEST_HASH2)
    assert dbcache.size == 2
    dbcache.add(pgdb, TEST_HASH3)
    assert dbcache.size == 3
    dbcache.trim_size(max_size=2)
    assert dbcache.size == 2
    result = CliRunner().invoke(
        main,
        [
            "--cache-prefix",
            TEST_PREFIX,
            "--cache-max-size",
            "-1",
            "--cache-max-age",
            "-1",
        ],
    )
    assert result.exit_code == 0
    assert dbcache.size == 2
    result = CliRunner().invoke(
        main,
        [
            "--cache-prefix",
            TEST_PREFIX,
            "--cache-max-size",
            "1",
            "--cache-max-age",
            "-1",
        ],
    )
    assert result.exit_code == 0
    assert dbcache.size == 1
    result = CliRunner().invoke(
        main,
        [
            "--cache-prefix",
            TEST_PREFIX,
            "--cache-max-size",
            "0",
            "--cache-max-age",
            "-1",
        ],
    )
    assert result.exit_code == 0
    assert dbcache.size == 0


def test_dbcache_trim_age(pgdb, dbcache):
    assert dbcache.size == 0
    with mock.patch.object(initdb, "datetime") as mock_dt:
        # create a few db with known dates
        mock_dt.utcnow.return_value = TODAY
        dbcache.add(pgdb, TEST_HASH1)
        assert dbcache.size == 1
        mock_dt.utcnow.return_value = TODAY_MINUS_2
        dbcache.add(pgdb, TEST_HASH2)
        assert dbcache.size == 2
        mock_dt.utcnow.return_value = TODAY_MINUS_4
        dbcache.add(pgdb, TEST_HASH3)
        assert dbcache.size == 3
        # get back to TODAY
        mock_dt.utcnow.return_value = TODAY
        # trim older than 5 days: no change
        dbcache.trim_age(timedelta(days=5))
        assert dbcache.size == 3
        # trim older than 3 days: drop one
        dbcache.trim_age(timedelta(days=3))
        assert dbcache.size == 2
        # do nothing
        result = CliRunner().invoke(
            main,
            [
                "--cache-prefix",
                TEST_PREFIX,
                "--cache-max-size",
                "-1",
                "--cache-max-age",
                "-1",
            ],
        )
        assert result.exit_code == 0
        assert dbcache.size == 2
        # drop older than 1 day, drop one
        result = CliRunner().invoke(
            main,
            [
                "--cache-prefix",
                TEST_PREFIX,
                "--cache-max-size",
                "-1",
                "--cache-max-age",
                "1",
            ],
        )
        assert result.exit_code == 0
        assert dbcache.size == 1
        # drop today too, drop everything
        result = CliRunner().invoke(
            main,
            [
                "--cache-prefix",
                TEST_PREFIX,
                "--cache-max-size",
                "-1",
                "--cache-max-age",
                "0",
            ],
        )
        assert result.exit_code == 0
        assert dbcache.size == 0


def test_create_cmd_cache(dbcache, tmpdir):
    assert dbcache.size == 0
    try:
        result = CliRunner().invoke(
            main,
            ["--cache-prefix", TEST_PREFIX, "-n", TEST_DBNAME_NEW, "-m", "auth_signup"],
        )
        assert result.exit_code == 0
        assert dbcache.size == 1
        with click_odoo.OdooEnvironment(database=TEST_DBNAME_NEW) as env:
            m = env["ir.module.module"].search(
                [("name", "=", "auth_signup"), ("state", "=", "installed")]
            )
            assert m, "auth_signup module not installed"
            env.cr.execute(
                """
                SELECT COUNT(*) FROM ir_attachment
                WHERE store_fname IS NOT NULL
            """
            )
            assert env.cr.fetchone()[0] == 0, "some attachments are not stored in db"
    finally:
        _dropdb(TEST_DBNAME_NEW)
    # try again, from cache this time
    with mock.patch.object(initdb, "odoo_createdb") as m:
        try:
            result = CliRunner().invoke(
                main,
                [
                    "--cache-prefix",
                    TEST_PREFIX,
                    "--new-database",
                    TEST_DBNAME_NEW,
                    "--modules",
                    "auth_signup",
                ],
            )
            assert result.exit_code == 0
            assert m.call_count == 0
            assert dbcache.size == 1
        finally:
            _dropdb(TEST_DBNAME_NEW)
        # now run again, with a new addon in path
        # and make sure the list of modules has been updated
        # after creating the database from cache
        odoo_cfg = tmpdir / "odoo.cfg"
        odoo_cfg.write(
            textwrap.dedent(
                """\
            [options]
            addons_path = {}
        """.format(
                    ADDONS_PATH
                )
            )
        )
        cmd = [
            sys.executable,
            "-m",
            "click_odoo_contrib.initdb",
            "-c",
            str(odoo_cfg),
            "--cache-prefix",
            TEST_PREFIX,
            "--new-database",
            TEST_DBNAME_NEW,
            "--modules",
            "auth_signup",
        ]
        try:
            subprocess.check_call(cmd)
            with click_odoo.OdooEnvironment(database=TEST_DBNAME_NEW) as env:
                assert env["ir.module.module"].search(
                    [("name", "=", "addon1")]
                ), "module addon1 not present in new database"
        finally:
            _dropdb(TEST_DBNAME_NEW)


def test_create_cmd_nocache(dbcache):
    assert dbcache.size == 0
    try:
        result = CliRunner().invoke(
            main, ["--no-cache", "-n", TEST_DBNAME_NEW, "-m", "auth_signup"]
        )
        assert result.exit_code == 0
        assert dbcache.size == 0
        with click_odoo.OdooEnvironment(database=TEST_DBNAME_NEW) as env:
            m = env["ir.module.module"].search(
                [("name", "=", "auth_signup"), ("state", "=", "installed")]
            )
            assert m, "auth_signup module not installed"
            env.cr.execute(
                """
                SELECT COUNT(*) FROM ir_attachment
                WHERE store_fname IS NULL
            """
            )
            assert (
                env.cr.fetchone()[0] == 0
            ), "some attachments are not stored in filestore"
    finally:
        _dropdb(TEST_DBNAME_NEW)


def test_dbcache_add_concurrency(pgdb, dbcache):
    assert dbcache.size == 0
    dbcache.add(pgdb, TEST_HASH1)
    assert dbcache.size == 1
    dbcache.add(pgdb, TEST_HASH1)
    assert dbcache.size == 1


def test_unless_exists_exists(pgdb):
    result = CliRunner().invoke(main, ["--unless-exists", "-n", TEST_DBNAME])
    assert result.exit_code == 0
    assert "Database already exists" in result.output
    result = CliRunner().invoke(main, ["-n", TEST_DBNAME])
    assert result.exit_code != 0
    assert "already exists" in result.output
