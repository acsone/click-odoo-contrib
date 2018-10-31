# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess
import textwrap

import pytest
from click_odoo import odoo, odoo_bin

# This hack is necessary because the way CliRunner patches
# stdout is not compatible with the Odoo logging initialization
# mechanism. Logging is therefore tested with subprocesses.
odoo.netsvc._logger_init = True


def _init_odoo_db(dbname, test_addons_dir=None):
    subprocess.check_call(["createdb", dbname])
    cmd = [odoo_bin, "-d", dbname, "-i", "base", "--stop-after-init"]
    if test_addons_dir:
        addons_path = [
            os.path.join(odoo.__path__[0], "addons"),
            os.path.join(odoo.__path__[0], "..", "addons"),
            test_addons_dir,
        ]
        cmd.append("--addons-path")
        cmd.append(",".join(addons_path))
    subprocess.check_call(cmd)


def _drop_db(dbname):
    subprocess.check_call(["dropdb", dbname])


@pytest.fixture(scope="module")
def odoodb(request):
    dbname = "click-odoo-contrib-test-{}".format(odoo.release.version_info[0])
    test_addons_dir = getattr(request.module, "test_addons_dir", "")
    _init_odoo_db(dbname, test_addons_dir)
    try:
        yield dbname
    finally:
        _drop_db(dbname)


@pytest.fixture(scope="function")
def odoocfg(request, tmpdir):
    addons_path = [
        os.path.join(odoo.__path__[0], "addons"),
        os.path.join(odoo.__path__[0], "..", "addons"),
    ]
    test_addons_dir = getattr(request.module, "test_addons_dir", "")
    if test_addons_dir:
        addons_path.append(test_addons_dir)
    odoo_cfg = tmpdir / "odoo.cfg"
    odoo_cfg.write(
        textwrap.dedent(
            """\
        [options]
        addons_path = {}
    """.format(
                ",".join(addons_path)
            )
        )
    )
    yield odoo_cfg
