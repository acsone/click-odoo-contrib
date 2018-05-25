# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

from click_odoo_contrib import manifest


HERE = os.path.dirname(__file__)
ADDONS_DIR = os.path.join(HERE, 'data/addons')


def test_manifest_find_addons():
    addons = list(manifest.find_addons(ADDONS_DIR))
    assert len(addons) == 1
    assert addons[0][0] == 'addon1'


def test_manifest_find_addons_uninstallable():
    addons = list(manifest.find_addons(ADDONS_DIR, installable_only=False))
    assert len(addons) == 2
    assert addons[0][0] == 'addon1'
    assert addons[1][0] == 'addon_uninstallable'
