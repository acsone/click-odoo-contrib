# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess
import sys
import threading
import time
from contextlib import closing

import psycopg2
import pytest
from click_odoo import odoo, odoo_bin

pytestmark = pytest.mark.skipif(
    odoo.release.version_info < (16, 0),
    reason="--watcher-prioritize-update requires Odoo 16 or later",
)

# this extends the addons path of the odoodb fixture
test_addons_dir = os.path.join(
    os.path.dirname(__file__), "data", "test_update_watcher", "v1"
)


def _addons_path(v):
    return ",".join(
        [
            os.path.join(odoo.__path__[0], "addons"),
            os.path.join(odoo.__path__[0], "..", "addons"),
            os.path.join(os.path.dirname(__file__), "data", "test_update_watcher", v),
        ]
    )


def _install(odoodb, addon):
    subprocess.check_call(
        [
            odoo_bin,
            "--addons-path",
            _addons_path("v1"),
            "-d",
            odoodb,
            "-i",
            addon,
            "--stop-after-init",
        ]
    )


def _update_cmd(odoodb, *args, max_seconds=1):
    return [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path("v2"),
        "-d",
        odoodb,
        "--watcher-max-seconds",
        str(max_seconds),
        *args,
    ]


def _column_exists(odoodb, column):
    with closing(psycopg2.connect(dbname=odoodb)) as conn, conn.cursor() as cr:
        cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'res_partner' AND column_name = %s",
            (column,),
        )
        return bool(cr.fetchone())


def test_watcher_update_blocked(odoodb):
    """A session keeps the update waiting to add a column."""
    _install(odoodb, "addon_blocked")
    with closing(psycopg2.connect(dbname=odoodb)) as conn:
        cr = conn.cursor()
        # An open transaction that read res_partner keeps a lock that
        # conflicts with the one ALTER TABLE needs
        cr.execute("SELECT id FROM res_partner LIMIT 1")
        # By default, the watcher aborts the update
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.check_call(_update_cmd(odoodb))
        cr.execute("SELECT 1")
        assert not _column_exists(odoodb, "watcher_blocked_field")
        # With priority, the blocking session is terminated instead, even with
        # a limit longer than Odoo's lock timeout
        subprocess.check_call(
            _update_cmd(odoodb, "--watcher-prioritize-update", max_seconds=60)
        )
        with pytest.raises((psycopg2.OperationalError, psycopg2.InterfaceError)):
            cr.execute("SELECT 1")
    assert _column_exists(odoodb, "watcher_blocked_field")


def test_watcher_prioritize_update_blocking(odoodb):
    """The update keeps a session waiting longer than the watcher limit."""
    _install(odoodb, "addon_blocking")
    update = subprocess.Popen(_update_cmd(odoodb, "--watcher-prioritize-update"))
    busy_errors = []

    def busy_session():
        # A long query that neither waits for the update nor blocks it
        try:
            with closing(psycopg2.connect(dbname=odoodb)) as busy_conn:
                with busy_conn.cursor() as busy_cr:
                    busy_cr.execute("SELECT pg_sleep(4)")
        except Exception as e:
            busy_errors.append(e)

    try:
        with closing(psycopg2.connect(dbname=odoodb)) as conn:
            cr = conn.cursor()
            deadline = time.monotonic() + 120
            while True:
                # Wait until the migration holds its lock on res_partner
                cr.execute(
                    """
                    SELECT 1
                    FROM pg_locks JOIN pg_class ON pg_class.oid = pg_locks.relation
                    WHERE pg_class.relname = 'res_partner'
                        AND pg_locks.mode = 'AccessExclusiveLock'
                        AND pg_locks.granted
                    """
                )
                if cr.fetchone():
                    break
                conn.rollback()
                assert update.poll() is None, "update finished before locking"
                assert time.monotonic() < deadline, "update never locked"
                time.sleep(0.1)
            conn.rollback()
            busy = threading.Thread(target=busy_session)
            busy.start()
            # The session waiting for the update is terminated, so that it
            # doesn't keep an Odoo worker busy
            with pytest.raises(psycopg2.OperationalError):
                cr.execute("SELECT id FROM res_partner LIMIT 1")
            busy.join()
        assert not busy_errors
        # The update is not terminated nor reported as aborted
        assert update.wait(timeout=120) == 0
    finally:
        if update.poll() is None:
            update.kill()
    assert _column_exists(odoodb, "watcher_blocking_column")
