import io
import subprocess

import click
import pytest

from click_odoo_contrib import backupdb


class FakeProcess:
    def __init__(self, returncode):
        self.returncode = None
        self.final_returncode = returncode
        self.stdout = io.BytesIO(b"synthetic partial dump")
        self.waited = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stdout.close()
        self.wait()

    def wait(self):
        self.waited = True
        self.returncode = self.final_returncode
        return self.returncode


class FakeBackup:
    format = "zip"

    def write(self, stream, filename):
        self.filename = filename
        self.data = stream.read()


def test_dump_db_checks_pg_dump_exit_status(monkeypatch):
    process = FakeProcess(returncode=7)
    backup = FakeBackup()
    popen_calls = []

    def fake_popen(args, **kwargs):
        popen_calls.append((args, kwargs))
        return process

    monkeypatch.setattr(backupdb.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        backupdb.odoo.tools.misc, "exec_pg_environ", lambda: {"SYNTHETIC": "1"}
    )

    with pytest.raises(click.ClickException, match="pg_dump failed with exit code 7"):
        backupdb._dump_db("synthetic-db", backup)

    assert process.waited
    assert backup.filename == "dump.sql"
    assert backup.data == b"synthetic partial dump"
    args, kwargs = popen_calls[0]
    assert args == ["pg_dump", "--no-owner", "synthetic-db"]
    assert kwargs["env"] == {"SYNTHETIC": "1"}
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["stdout"] == subprocess.PIPE
