# -*- coding: utf-8 -*-
# Copyright © 2015-2020 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)
"""List of Odoo official addons."""

try:
    from importlib.resources import open_text
except ImportError:
    from importlib_resources import open_text  # python < 3.9


def _addons(suffix):
    with open_text("click_odoo_contrib.core_addons", "addons-%s.txt" % suffix) as f:
        return {a.strip() for a in f if not a.startswith("#")}


core_addons = {
    "8.0": _addons("8c"),
    "9.0": _addons("9c") | _addons("9e"),
    "10.0": _addons("10c") | _addons("10e"),
    "11.0": _addons("11c") | _addons("11e"),
    "12.0": _addons("12c") | _addons("12e"),
    "13.0": _addons("13c") | _addons("13e"),
    "14.0": _addons("14c") | _addons("14e"),
    "15.0": _addons("15c") | _addons("15e"),
}
