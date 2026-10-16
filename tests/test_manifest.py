# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

import pytest
from click_odoo import odoo

from click_odoo_contrib import manifest

HERE = os.path.dirname(__file__)
ADDONS_DIR = os.path.join(HERE, "data/test_manifest")


def test_manifest_find_addons():
    addons = list(manifest.find_addons(ADDONS_DIR))
    assert len(addons) == 1
    assert addons[0][0] == "addon1"


def test_manifest_find_addons_uninstallable():
    addons = list(manifest.find_addons(ADDONS_DIR, installable_only=False))
    assert len(addons) == 2
    assert addons[0][0] == "addon1"
    assert addons[1][0] == "addon_uninstallable"


def test_manifest_expand_dependencies():
    res = manifest.expand_dependencies(["auth_signup", "base_import"])
    assert "auth_signup" in res
    assert "mail" in res  # dependency of auth_signup
    assert "base_import" in res
    assert "base" in res  # obviously
    assert "web" in res  # base_import depends on web
    if odoo.release.version_info < (12, 0):
        assert "auth_crypt" not in res
    else:
        assert "iap" not in res  # iap is auto_install


def test_manifest_expand_dependencies_auto_install():
    res = manifest.expand_dependencies(["auth_signup"], include_auto_install=True)
    assert "auth_signup" in res
    assert "base" in res  # obviously
    if odoo.release.version_info < (12, 0):
        assert "auth_crypt" in res  # auth_crypt is autoinstall
    else:
        assert "iap" in res  # iap is auto_install
    assert "web" in res  # web is autoinstall
    assert "base_import" in res  # base_import is indirect autoinstall


def test_manifest_expand_dependencies_not_found():
    with pytest.raises(manifest.ModuleNotFound):
        manifest.expand_dependencies(["not_a_module"])


@pytest.fixture
def fake_addons(tmp_path, monkeypatch):
    addons = {
        "base": {},
        "web": {"depends": ["base"], "auto_install": True},
        "account": {"depends": ["base"]},
        "payment": {"depends": ["base"]},
        "account_payment": {
            "depends": ["account", "payment"],
            "auto_install": ["account"],
        },
        "always": {"depends": ["base"], "auto_install": []},
        "opt_in": {"depends": ["base"], "auto_install": False},
    }
    for name, manifest_dict in addons.items():
        (tmp_path / name).mkdir()
        (tmp_path / name / "__manifest__.py").write_text(repr(manifest_dict))
    monkeypatch.setattr(
        manifest.odoo.modules, "get_module_path", lambda name: str(tmp_path / name)
    )
    monkeypatch.setattr(
        manifest.odoo.modules.module, "get_modules", lambda: sorted(addons)
    )


def test_manifest_expand_dependencies_auto_install_list(fake_addons):
    res = manifest.expand_dependencies(["account"], include_auto_install=True)
    assert res == {"base", "web", "account", "payment", "account_payment", "always"}


def test_manifest_expand_dependencies_auto_install_empty_list(fake_addons):
    res = manifest.expand_dependencies(["base"], include_auto_install=True)
    assert res == {"base", "web", "always"}
