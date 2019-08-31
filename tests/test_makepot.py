# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import shutil
import subprocess

import click_odoo
from click.testing import CliRunner

from click_odoo_contrib.makepot import main

# this extends the addons path of the odoodb and odoocfg fixtures
test_addons_dir = os.path.join(os.path.dirname(__file__), "data", "test_makepot")


def test_makepot_base(odoodb, odoocfg, tmpdir):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")

    subprocess.check_call(
        [
            click_odoo.odoo_bin,
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "-i",
            addon_name,
            "--stop-after-init",
        ]
    )

    if os.path.exists(pot_filepath):
        os.remove(pot_filepath)

    result = CliRunner().invoke(
        main, ["-d", odoodb, "-c", str(odoocfg), "--addons-dir", test_addons_dir]
    )

    assert result.exit_code == 0
    assert os.path.isdir(i18n_path)
    assert os.path.isfile(pot_filepath)
    with open(pot_filepath) as f:
        assert "myfield" in f.read()


def test_makepot_msgmerge(odoodb, odoocfg, tmpdir):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")
    fr_filepath = os.path.join(i18n_path, "fr.po")

    subprocess.check_call(
        [
            click_odoo.odoo_bin,
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "-i",
            addon_name,
            "--stop-after-init",
        ]
    )

    if not os.path.exists(i18n_path):
        os.makedirs(i18n_path)
    if os.path.exists(pot_filepath):
        os.remove(pot_filepath)
    # create empty fr.po, that will be updated by msgmerge
    with open(fr_filepath, "w"):
        pass
    assert os.path.getsize(fr_filepath) == 0

    result = CliRunner().invoke(
        main,
        [
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "--addons-dir",
            test_addons_dir,
            "--msgmerge",
        ],
    )

    assert result.exit_code == 0
    assert os.path.getsize(fr_filepath) != 0
    with open(fr_filepath) as f:
        assert "myfield" in f.read()


def test_makepot_msgmerge_if_new_pot(odoodb, odoocfg, tmpdir):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")
    fr_filepath = os.path.join(i18n_path, "fr.po")

    subprocess.check_call(
        [
            click_odoo.odoo_bin,
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "-i",
            addon_name,
            "--stop-after-init",
        ]
    )

    if not os.path.exists(i18n_path):
        os.makedirs(i18n_path)
    if os.path.exists(pot_filepath):
        os.remove(pot_filepath)
    # create empty .pot
    with open(pot_filepath, "w"):
        pass
    # create empty fr.po
    with open(fr_filepath, "w"):
        pass
    assert os.path.getsize(fr_filepath) == 0

    result = CliRunner().invoke(
        main,
        [
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "--addons-dir",
            test_addons_dir,
            "--msgmerge-if-new-pot",
        ],
    )

    assert result.exit_code == 0
    # po file not changed because .pot did exist
    assert os.path.getsize(fr_filepath) == 0

    # now remove pot file so a new one will
    # be created and msgmerge will run
    os.remove(pot_filepath)

    result = CliRunner().invoke(
        main,
        [
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "--addons-dir",
            test_addons_dir,
            "--msgmerge-if-new-pot",
        ],
    )

    with open(fr_filepath) as f:
        assert "myfield" in f.read()


def test_makepot_detect_bad_po(odoodb, odoocfg, capfd):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    fr_filepath = os.path.join(i18n_path, "fr.po")

    subprocess.check_call(
        [
            click_odoo.odoo_bin,
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "-i",
            addon_name,
            "--stop-after-init",
        ]
    )

    shutil.copy(fr_filepath + ".bad", fr_filepath)

    capfd.readouterr()
    result = CliRunner().invoke(
        main, ["-d", odoodb, "-c", str(odoocfg), "--addons-dir", test_addons_dir]
    )

    assert result.exit_code != 0
    capture = capfd.readouterr()
    assert "duplicate message definition" in capture.err
    assert "msgmerge: found 1 fatal error" in capture.err
