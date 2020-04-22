# Copyright 2020 ACSONE SA/NV.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import pytest

from click_odoo_contrib.core_addons import core_addons


@pytest.mark.parametrize("series", ["8.0", "9.0", "10.0", "11.0", "12.0", "13.0"])
def test_core_addons(series):
    assert "base" in core_addons[series]
