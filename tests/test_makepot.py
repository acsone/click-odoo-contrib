# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import subprocess

from click.testing import CliRunner
import click_odoo

from click_odoo_contrib.makepot import main

# this extends the addons path of the odoodb and odoocfg fixtures
test_addons_dir = os.path.join(
    os.path.dirname(__file__), 'data', 'test_makepot')


def test_makepot(odoodb, odoocfg, tmpdir):
    addon_name = 'addon_test_makepot'

    subprocess.check_call([
        click_odoo.odoo_bin,
        '-d', odoodb,
        '-c', str(odoocfg),
        '-i', addon_name,
        '--stop-after-init',
    ])

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--addons-dir', test_addons_dir,
    ])

    assert result.exit_code == 0

    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, 'i18n')
    pot_filepath = os.path.join(i18n_path, addon_name + '.pot')

    assert os.path.isdir(i18n_path)
    assert os.path.isfile(pot_filepath)
