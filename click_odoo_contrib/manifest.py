# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import ast
import os

from click_odoo import odoo

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py")


class NoManifestFound(Exception):
    pass


class ModuleNotFound(Exception):
    pass


def get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def parse_manifest(s):
    return ast.literal_eval(s)


def read_manifest(addon_dir):
    manifest_path = get_manifest_path(addon_dir)
    if not manifest_path:
        raise NoManifestFound("no Odoo manifest found in %s" % addon_dir)
    with open(manifest_path) as mf:
        return parse_manifest(mf.read())


def find_addons(addons_dir, installable_only=True):
    """ yield (addon_name, addon_dir, manifest) """
    for addon_name in sorted(os.listdir(addons_dir)):
        addon_dir = os.path.join(addons_dir, addon_name)
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        if installable_only and not manifest.get("installable", True):
            continue
        yield addon_name, addon_dir, manifest


def expand_dependencies(module_names, include_auto_install=False, include_active=False):
    """ Return a set of module names with their transitive
    dependencies.  This method does not need an Odoo database,
    but requires the addons path to be initialized.
    """

    def add_deps(name):
        if name in res:
            return
        res.add(name)
        path = odoo.modules.get_module_path(name)
        if not path:
            raise ModuleNotFound(name)
        manifest = read_manifest(path)
        for dep in manifest.get("depends", ["base"]):
            add_deps(dep)

    res = set()
    for module_name in module_names:
        add_deps(module_name)
    if include_active:
        for module_name in sorted(odoo.modules.module.get_modules()):
            module_path = odoo.modules.get_module_path(module_name)
            manifest = read_manifest(module_path)
            if manifest.get("active"):
                add_deps(module_name)
    if include_auto_install:
        auto_install_list = []
        for module_name in sorted(odoo.modules.module.get_modules()):
            module_path = odoo.modules.get_module_path(module_name)
            manifest = read_manifest(module_path)
            if manifest.get("auto_install"):
                auto_install_list.append((module_name, manifest))
        retry = True
        while retry:
            retry = False
            for module_name, manifest in auto_install_list:
                if module_name in res:
                    continue
                depends = set(manifest.get("depends", ["base"]))
                if depends.issubset(res):
                    # all dependencies of auto_install module are
                    # installed so we add it
                    add_deps(module_name)
                    # retry, in case an auto_install module depends
                    # on other auto_install modules
                    retry = True
    return res
