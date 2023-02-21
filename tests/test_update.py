# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import os
import subprocess
import sys

import pytest
from click.testing import CliRunner
from click_odoo import OdooEnvironment, odoo, odoo_bin

from click_odoo_contrib.update import _load_installed_checksums, main

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
        _addons_path("v1"),
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
        assert checksums.get("addon_app") == "bb1ff827fd6084e69180557c3183989100ddb62b"
        assert checksums.get("addon_d1") == "ff46eefbe846e1a46ff3de74e117fd285b72f298"
        assert checksums.get("addon_d2") == "edf58645e2e55a2d282320206f73df09a746a4ab"
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
    if odoo.release.version_info >= (12, 0):
        # Odoo >= 12 does -u in a transaction
        _check_expected(odoodb, "v6")


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
