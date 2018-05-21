# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import subprocess

import pytest

from click_odoo import odoo, odoo_bin

# This hack is necessary because the way CliRunner patches
# stdout is not compatible with the Odoo logging initialization
# mechanism. Logging is therefore tested with subprocesses.
odoo.netsvc._logger_init = True


def _init_odoo_db(dbname):
    subprocess.check_call([
        'createdb', dbname,
    ])
    subprocess.check_call([
        odoo_bin,
        '-d', dbname,
        '--stop-after-init',
    ])


def _drop_db(dbname):
    subprocess.check_call([
        'dropdb', dbname,
    ])


@pytest.fixture(scope='module')
def odoodb():
    dbname = 'click-odoo-contrib-test-{}'.\
        format(odoo.release.version_info[0])
    _init_odoo_db(dbname)
    try:
        yield dbname
    finally:
        _drop_db(dbname)
