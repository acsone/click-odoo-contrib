# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess
import sys

from click_odoo import OdooEnvironment, odoo, odoo_bin

from click_odoo_contrib.update import (
    _load_installed_checksums,
    PARAM_INSTALLED_CHECKSUMS,
)

# this extends the addons path of the odoodb and odoocfg fixtures
test_addons_dir = os.path.join(os.path.dirname(__file__), "data", "test_update", "v3")


def _only_compute_hashes(odoodb, odoocfg, ignore_addons, ignore_core_addons):
    cmd = [
        sys.executable,
        "-m",
        "click_odoo_contrib.update",
        "-c",
        odoocfg,
        "-d",
        odoodb,
        "--only-compute-hashes",
    ]
    if ignore_addons:
        cmd += ["--ignore-addons", ignore_addons]
    if ignore_core_addons:
        cmd += ["--ignore-core-addons"]
    subprocess.check_call(cmd)


def test_only_compute_hashes(odoodb, odoocfg):
    subprocess.check_call(
        [
            odoo_bin,
            "-d",
            odoodb,
            "-c",
            odoocfg,
            "-i",
            "addon_app",
            "--stop-after-init",
        ]
    )

    conn = odoo.sql_db.db_connect(odoodb)
    with conn.cursor() as cr:
        cr.execute(
            "DELETE from ir_config_parameter where key=%s", (PARAM_INSTALLED_CHECKSUMS,)
        )

    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        assert "base" not in checksums
        assert "addon_app" not in checksums
        assert "addon_d1" not in checksums
        assert "addon_d2" not in checksums

    _only_compute_hashes(
        odoodb, odoocfg, ignore_addons="addon_d1,addon_d2", ignore_core_addons=True
    )
    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        assert "base" not in checksums
        assert "addon_app" in checksums
        assert "addon_d1" not in checksums
        assert "addon_d2" not in checksums

    _only_compute_hashes(odoodb, odoocfg, ignore_addons=None, ignore_core_addons=True)
    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        assert "base" not in checksums
        assert "addon_app" in checksums
        assert "addon_d1" in checksums
        assert "addon_d2" in checksums

    _only_compute_hashes(odoodb, odoocfg, ignore_addons=None, ignore_core_addons=False)
    with OdooEnvironment(odoodb) as env:
        checksums = _load_installed_checksums(env.cr)
        assert "base" in checksums
        assert "addon_app" in checksums
        assert "addon_d1" in checksums
        assert "addon_d2" in checksums
