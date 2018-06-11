# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import click_odoo
import subprocess
import textwrap

from click.testing import CliRunner

from click_odoo_contrib.makepot import main

ADDONS_DIR = os.path.join(
    os.path.dirname(__file__), 'data', 'test_makepot')

ADDONS_PATH = ','.join([
    os.path.join(click_odoo.odoo.__path__[0], 'addons'),
    os.path.join(click_odoo.odoo.__path__[0], '..', 'addons'),
    ADDONS_DIR,
])


def test_makepot(odoodb, tmpdir):
    odoo_cfg = tmpdir / 'odoo.cfg'
    odoo_cfg.write(textwrap.dedent("""\
        [options]
        addons_path = {}
    """.format(ADDONS_PATH)))
    addon_name = 'addon_test_makepot'

    subprocess.check_call([
        click_odoo.odoo_bin,
        '-d', str(odoodb),
        '-c', str(odoo_cfg),
        '-i', addon_name,
        '--stop-after-init',
    ])

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoo_cfg),
        '--addons-dir', ADDONS_DIR,
    ])

    assert result.exit_code == 0

    addon_path = os.path.join(ADDONS_DIR, addon_name)
    i18n_path = os.path.join(addon_path, 'i18n')
    pot_filepath = os.path.join(i18n_path, addon_name + '.pot')

    assert os.path.isdir(i18n_path)
    assert os.path.isfile(pot_filepath)
