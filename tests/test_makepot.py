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


def test_makepot_modules(odoodb, odoocfg, tmpdir):
    subprocess.check_call(
        [
            click_odoo.odoo_bin,
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "-i",
            "addon_test_makepot,addon_test_makepot_2",
            "--stop-after-init",
        ]
    )
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")

    if os.path.exists(pot_filepath):
        os.remove(pot_filepath)

    addon_name_2 = "addon_test_makepot_2"
    addon_path_2 = os.path.join(test_addons_dir, addon_name_2)
    i18n_path_2 = os.path.join(addon_path_2, "i18n")
    pot_filepath_2 = os.path.join(i18n_path_2, addon_name_2 + ".pot")

    if os.path.exists(pot_filepath_2):
        os.remove(pot_filepath_2)

    result = CliRunner().invoke(
        main,
        [
            "-d",
            odoodb,
            "-c",
            str(odoocfg),
            "--addons-dir",
            test_addons_dir,
            "--modules",
            "addon_test_makepot_2",
        ],
    )
    assert result.exit_code == 0
    assert not os.path.isdir(pot_filepath)
    assert os.path.isdir(i18n_path_2)
    assert os.path.isfile(pot_filepath_2)
    with open(pot_filepath_2) as f:
        assert "myfield" in f.read()


def test_makepot_absent_module(odoodb):
    result = CliRunner().invoke(
        main,
        [
            "-d",
            odoodb,
            "--addons-dir",
            test_addons_dir,
            "--modules",
            "not_existing_module",
        ],
    )
    assert result.exit_code != 0
    assert "Module(s) was not found" in result.stdout


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


def test_makepot_msgmerge_no_fuzzy(odoodb, odoocfg, tmpdir):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")
    fr_filepath = os.path.join(i18n_path, "fr.po")

    # Copy .fuzzy to .po
    shutil.copyfile(os.path.join(i18n_path, "fr.po.fuzzy"), fr_filepath)

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
            "--no-fuzzy-matching",
        ],
    )

    assert result.exit_code == 0
    assert os.path.getsize(fr_filepath) != 0
    with open(fr_filepath) as f:
        assert "#, fuzzy" not in f.read()


def test_makepot_msgmerge_purge_old(odoodb, odoocfg, tmpdir):
    addon_name = "addon_test_makepot"
    addon_path = os.path.join(test_addons_dir, addon_name)
    i18n_path = os.path.join(addon_path, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + ".pot")
    fr_filepath = os.path.join(i18n_path, "fr.po")

    # Copy .old to .po
    shutil.copyfile(os.path.join(i18n_path, "fr.po.old"), fr_filepath)

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
            "--purge-old-translations",
        ],
    )

    assert result.exit_code == 0
    assert os.path.getsize(fr_filepath) != 0
    with open(fr_filepath) as f:
        assert "#~ msgid" not in f.read()


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
