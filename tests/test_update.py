# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import os
import subprocess
import sys

import pytest
from click.testing import CliRunner
from click_odoo import OdooEnvironment, odoo, odoo_bin

from .conftest import min_odoo_version
from click_odoo_contrib.update import (
    _load_installed_checksums,
    _parse_pre_update_scripts,
    main,
)

# this extends the addons path of the odoodb and odoocfg fixtures
# we use the v1 dir, so the first install work (since it's only since version 12
# that Odoo updates the modules list before installing)
test_addons_dir = os.path.join(os.path.dirname(__file__), "data", "test_update", "v1")


def _addons_dir(v):
    return os.path.join(os.path.dirname(__file__), "data", "test_update", v)


def _addons_path(v):
    return ",".join(
        [
            os.path.join(odoo.__path__[0], "addons"),
            os.path.join(odoo.__path__[0], "..", "addons"),
            _addons_dir(v),
        ]
    )


def _check_expected(odoodb, v):
    with OdooEnvironment(database=odoodb) as env:
        with open(os.path.join(_addons_dir(v), "expected.json")) as f:
            expected = json.load(f)
        for addon_name, expected_data in expected.items():
            env.cr.execute(
                "SELECT state, latest_version FROM ir_module_module WHERE name=%s",
                (addon_name,),
            )
            state, version = env.cr.fetchone()
            expected_state = expected_data.get("state")
            if expected_state:
                assert state == expected_state, addon_name
            expected_version = expected_data.get("version")
            if expected_version:
                assert version.split(".")[2:] == expected_version.split("."), addon_name


def _install_one(odoodb, v):
    cmd = [
        odoo_bin,
        "--addons-path",
        _addons_path(v),
        "-d",
        odoodb,
        "-i",
        "addon_app",
        "--stop-after-init",
    ]
    subprocess.check_call(cmd)


def _update_one(odoodb, v, ignore_addons=None, ignore_core_addons=False):
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path(v),
        "-d",
        odoodb,
    ]
    if ignore_addons:
        cmd.extend(["--ignore-addons", ignore_addons])
    if ignore_core_addons:
        cmd.append("--ignore-core-addons")
    subprocess.check_call(cmd)


def _update_list(odoodb, v):
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path(v),
        "-d",
        odoodb,
        "--list-only",
    ]
    subprocess.check_call(cmd)


def test_update(odoodb):
    _install_one(odoodb, "v1")
    _check_expected(odoodb, "v1")
    # With --list-only option update shouldn't be performed:
    _update_list(odoodb, "v2")
    _check_expected(odoodb, "v1")
    # With --ignore-addons addon_app, update should not be performed
    _update_one(odoodb, "v1", ignore_addons="addon_app")
    _check_expected(odoodb, "v1")
    # Default update should:
    _update_one(odoodb, "v2")
    _check_expected(odoodb, "v2")
    _update_one(odoodb, "v3")
    _check_expected(odoodb, "v3")
    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        print(checksums)
        assert "base" in checksums
        assert checksums.get("addon_app") == "f3e5fdbde44776fd42e3de285e8898aa11b3a9ba"
        assert checksums.get("addon_d1") == "2ec1acd11d21dd85d99851c72773adb5f30d2114"
        assert checksums.get("addon_d2") == "1924672701f2a79160cd53885e450c02b9874f6e"
    # 3.1 sets addons_d1 as uninstallable: it stays installed
    _update_one(odoodb, "v3.1")
    _check_expected(odoodb, "v3.1")
    _update_one(odoodb, "v4")
    _check_expected(odoodb, "v4")
    _update_one(odoodb, "v5")
    _check_expected(odoodb, "v5")
    _update_one(odoodb, "v6", ignore_core_addons=True)
    _check_expected(odoodb, "v6")
    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        assert "base" not in checksums  # because ignore_Core_addons=True
    with pytest.raises(subprocess.CalledProcessError):
        _update_one(odoodb, "v7")
    if (19, 0) > odoo.release.version_info >= (12, 0):
        # Odoo >= 12, < 19 does -u in a transaction
        # See https://github.com/odoo/odoo/issues/228833
        _check_expected(odoodb, "v6")
    else:
        _check_expected(odoodb, "v7")


def test_update_db_not_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["-d", "dbthatdoesnotexist"])
    assert result.exit_code != 0
    runner = CliRunner()
    result = runner.invoke(main, ["--if-exists", "-d", "dbthatdoesnotexist"])
    assert result.exit_code == 0


def test_update_i18n_overwrite(odoodb):
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--i18n-overwrite",
        "-d",
        odoodb,
    ]
    subprocess.check_call(cmd)
    # TODO how to test i18n-overwrite was effectively applied?


def test_parallel_watcher(odoodb):
    # Test that the parallel updater does not disturb normal operation
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--watcher-max-seconds",
        "30",
        "-d",
        odoodb,
    ]
    subprocess.check_call(cmd)
    # TODO Test an actual lock


def test_pre_update_scripts_invalid_path():
    # --pre-update-scripts with a non-existing path produces a clean error
    runner = CliRunner()
    result = runner.invoke(
        main, ["--pre-update-scripts", "/nonexistent/script.py", "-d", "dummy"]
    )
    assert result.exit_code != 0
    assert "nonexistent" in result.output
    # No traceback expected — Click handles BadParameter cleanly
    assert "Traceback" not in result.output


def test_pre_update_scripts_valid_paths(tmp_path):
    # _parse_pre_update_scripts accepts existing files and returns Path objects.
    script1 = tmp_path / "pre_a.py"
    script2 = tmp_path / "pre_b.py"
    script1.write_text("def migrate(cr, version): pass\n")
    script2.write_text("def migrate(cr, version): pass\n")

    result = _parse_pre_update_scripts(
        ctx=None,
        param=None,
        value=f"{script1},{script2}",
    )
    assert result == [script1, script2]


def test_pre_update_scripts_directory_rejected(tmp_path):
    # _parse_pre_update_scripts rejects a directory (files only)
    import click

    with pytest.raises((click.exceptions.BadParameter, SystemExit)):
        _parse_pre_update_scripts(ctx=None, param=None, value=str(tmp_path))


@min_odoo_version("16.0")
def test_pre_update_scripts_executed(odoodb, tmp_path):
    # A valid pre-update script is actually called before the Odoo update.
    marker = tmp_path / "executed.txt"
    script = tmp_path / "pre_script.py"
    script.write_text(
        f"""\
def migrate(cr, version):
    open({str(marker)!r}, "w").close()
"""
    )
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path("v1"),
        "-d",
        odoodb,
        "--pre-update-scripts",
        str(script),
    ]
    subprocess.check_call(cmd)
    assert marker.exists(), "pre-update script was not executed"


@min_odoo_version("16.0")
def test_pre_update_scripts_error_aborts_update(odoodb, tmp_path):
    # A pre-update script that raises an exception aborts the command.
    script = tmp_path / "pre_failing.py"
    script.write_text(
        """\
def migrate(cr, version):
    raise RuntimeError("intentional failure")
"""
    )
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path("v1"),
        "-d",
        odoodb,
        "--pre-update-scripts",
        str(script),
    ]
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(cmd)


@min_odoo_version("18.0")
def test_pre_update_scripts_missing_migrate_aborts(odoodb, tmp_path):
    # A script without a migrate() function aborts the command.
    script = tmp_path / "pre_no_migrate.py"
    script.write_text("# no migrate function\n")
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "--addons-path",
        _addons_path("v1"),
        "-d",
        odoodb,
        "--pre-update-scripts",
        str(script),
    ]
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(cmd)
