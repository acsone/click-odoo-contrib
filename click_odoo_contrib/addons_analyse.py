#!/usr/bin/env click-odoo
# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import logging
import os
import subprocess
import textwrap
from collections import defaultdict

import click
import click_odoo
import pkg_resources
import unicodecsv
from click_odoo import odoo

_logger = logging.getLogger(__name__)


def _get_addon_source_path(addon_name):
    odoo_addon_package = "odoo.addons"
    manifest_filename = "__manifest__.py"
    if odoo.tools.parse_version(odoo.release.version) < odoo.tools.parse_version(
        "10.0"
    ):
        odoo_addon_package = "openerp.addons"
        manifest_filename = "__openerp__.py"
    pkg_name = "{}.{}".format(odoo_addon_package, addon_name)
    manifest_path = pkg_resources.resource_filename(pkg_name, manifest_filename)
    return os.path.dirname(manifest_path)


def _skip_code_analysis(module):
    author = module.author.lower().strip()
    if "odoo sa" in author or "openerp sa" in author:
        if "(oca)" not in author:
            # don't collect stats for odoo addons
            return True
    return False


def _get_addon_base_info(module):
    author = module.author.strip()
    if "(oca)" in author.lower():
        # To allow efficient group by author
        author = "OCA"
    if "odoo sa" in author.lower() or "openerp sa" in author.lower():
        author = "Odoo SA"
    return {
        "name": module.name,
        "author": author,
        "version": module.latest_version,
        "category": module.category_id.name or "",
        "summary": textwrap.dedent(module.summary),
    }


def _addons_info_to_rows(addons_info):
    info_values = addons_info.values()
    if not isinstance(info_values, list):
        info_values = list(info_values)
    info_values.sort(key=lambda a: (a["author"], a["name"]))
    return info_values


def _extract_stats(path):
    # return a dict of line count by language
    _logger.info("Extract statistics in %s", path)
    languages = {"Python (tests)", "Python (business)"}
    cmd = [
        "cloc",
        "--json",
        "--by-file",
        "--quiet",
        "--fullpath",
        "--not-match-d",
        "static/lib|static/src/lib",
        "--follow-links",
        path,
    ]
    res = subprocess.check_output(cmd, universal_newlines=True)
    stats = json.loads(res)
    result = defaultdict(lambda: defaultdict(lambda: 0))
    for fpath, values in stats.items():
        if fpath in ["SUM", "header"]:
            continue
        fpath = fpath.replace(path, "")
        addon_name = fpath.split("/")[1]
        language = values["language"]
        languages.add(language)
        if language == "Python":
            if "tests" in fpath:
                result[addon_name][language + " (tests)"] += values["code"]
            else:
                result[addon_name][language + " (business)"] += values["code"]
        result[addon_name][language] += values["code"]
    return languages, result


@click.command()
@click_odoo.env_options(
    default_log_level="warn", with_database=True, with_rollback=False
)
@click.argument("output", type=click.File("wb"), required=True)
def main(env, output):
    """ Analyse installed addons and generate an csv file with stats by addon
    """
    installed_modules = env["ir.module.module"].search([("state", "=", "installed")])
    all_languages = set()
    addons_info = {}

    modules_by_addons_path = defaultdict(env["ir.module.module"].browse)

    for module in installed_modules:
        addons_path = _get_addon_source_path(module.name)
        info = _get_addon_base_info(module)
        info["addon_path"] = addons_path
        addons_info[module.name] = info

        # collect addon_path to the addon to group call to cloc by
        # addons directory
        modules_by_addons_path[os.path.dirname(addons_path)] |= module

    for addons_path, modules in modules_by_addons_path.items():
        languages, stats = _extract_stats(addons_path)
        for module in modules:
            if _skip_code_analysis(module):
                continue
            info = addons_info[module.name]
            stat = stats[module.name]
            info.update(stat)
        all_languages |= languages

    fieldnames = (
        ["name", "author", "version", "summary", "category"]
        + list(all_languages)
        + ["addon_path"]
    )
    writer = unicodecsv.DictWriter(output, fieldnames=fieldnames, encoding="utf-8")
    writer.writeheader()
    for st in _addons_info_to_rows(addons_info):
        writer.writerow(st)


if __name__ == "__main__":
    main()
