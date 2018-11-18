# Copyright 2018 ACSONE SA/NV.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os

from click_odoo_contrib import _addon_hash
from click_odoo_contrib.update import DEFAULT_EXCLUDE_PATTERNS

sample_dir = os.path.join(os.path.dirname(__file__), "data", "test_addon_hash")


def test_basic():
    files = list(
        _addon_hash._walk(
            sample_dir, exclude_patterns=["*/__pycache__/*"], keep_langs=[]
        )
    )
    assert files == [
        "README.rst",
        "data/f1.xml",
        "data/f2.xml",
        "i18n/en.po",
        "i18n/en_US.po",
        "i18n/fr.po",
        "i18n/fr_BE.po",
        "i18n/test.pot",
        "i18n_extra/en.po",
        "i18n_extra/fr.po",
        "i18n_extra/nl_NL.po",
        "models/stuff.py",
        "models/stuff.pyc",
        "models/stuff.pyo",
        "static/src/some.js",
    ]


def test_exclude():
    files = list(
        _addon_hash._walk(
            sample_dir,
            exclude_patterns=DEFAULT_EXCLUDE_PATTERNS.split(","),
            keep_langs=["fr_FR", "nl"],
        )
    )
    assert files == [
        "README.rst",
        "data/f1.xml",
        "data/f2.xml",
        "i18n/fr.po",
        "i18n/fr_BE.po",
        "i18n_extra/fr.po",
        "i18n_extra/nl_NL.po",
        "models/stuff.py",
    ]


def test2():
    checksum = _addon_hash.addon_hash(
        sample_dir,
        exclude_patterns=["*.pyc", "*.pyo", "*.pot", "static/*"],
        keep_langs=["fr_FR", "nl"],
    )
    assert checksum == "fecb89486c8a29d1f760cbd01c1950f6e8421b14"
