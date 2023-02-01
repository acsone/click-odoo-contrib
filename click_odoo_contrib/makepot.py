# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64
import os
import re
import subprocess

import click
import click_odoo

from . import gitutils, manifest

LINE_PATTERNS_TO_REMOVE = [
    r'"POT-Creation-Date:.*?"[\n\r]',
    r'"PO-Revision-Date:.*?"[\n\r]',
]

PO_FILE_EXT = ".po"
POT_FILE_EXT = ".pot"


def export_pot(
    env,
    module,
    addons_dir,
    msgmerge,
    commit,
    msgmerge_if_new_pot,
    commit_message,
    fuzzy_matching,
    purge_old_translations,
):
    addon_name = module.name
    addon_dir = os.path.join(addons_dir, addon_name)
    i18n_path = os.path.join(addon_dir, "i18n")
    pot_filepath = os.path.join(i18n_path, addon_name + POT_FILE_EXT)

    lang_export = env["base.language.export"].create(
        {"lang": "__new__", "format": "po", "modules": [(6, 0, [module.id])]}
    )
    lang_export.act_getfile()

    if not os.path.isdir(i18n_path):
        os.makedirs(i18n_path)

    pot_is_new = not os.path.exists(pot_filepath)

    files_to_commit = set()

    files_to_commit.add(pot_filepath)
    with open(pot_filepath, "w", encoding="utf-8") as pot_file:
        file_content = base64.b64decode(lang_export.data).decode("utf-8")
        for pattern in LINE_PATTERNS_TO_REMOVE:
            file_content = re.sub(pattern, "", file_content, flags=re.MULTILINE)
        pot_file.write(file_content)

    invalid_po = 0
    for lang_filename in os.listdir(i18n_path):
        if not lang_filename.endswith(PO_FILE_EXT):
            continue
        lang_filepath = os.path.join(i18n_path, lang_filename)
        try:
            if msgmerge or (msgmerge_if_new_pot and pot_is_new):
                files_to_commit.add(lang_filepath)
                cmd = ["msgmerge", "--quiet", "-U", lang_filepath, pot_filepath]
                if not fuzzy_matching:
                    cmd.append("--no-fuzzy-matching")
                subprocess.check_call(cmd)
                # Purge old translations
                if purge_old_translations:
                    cmd = [
                        "msgattrib",
                        "--output-file=%s" % lang_filepath,
                        "--no-obsolete",
                        lang_filepath,
                    ]
                    subprocess.check_call(cmd)
            else:
                # check .po is valid
                subprocess.check_output(
                    ["msgmerge", "--quiet", lang_filepath, pot_filepath]
                )
        except subprocess.CalledProcessError:
            invalid_po += 1
    if invalid_po:
        raise click.ClickException("%d invalid .po file(s) found" % invalid_po)

    if commit:
        gitutils.commit_if_needed(
            list(files_to_commit),
            commit_message.format(addon_name=addon_name),
            cwd=addons_dir,
        )


@click.command()
@click_odoo.env_options(with_rollback=False, default_log_level="error")
@click.option("--addons-dir", default=".", show_default=True)
@click.option(
    "--modules",
    "-m",
    help="Comma separated list of addons to export translation.",
)
@click.option(
    "--msgmerge / --no-msgmerge",
    show_default=True,
    help="Merge .pot changes into all .po files.",
)
@click.option(
    "--msgmerge-if-new-pot / --no-msg-merge-if-new-pot",
    show_default=True,
    help="Merge .pot changes into all .po files, only if "
    "a new .pot file has been created.",
)
@click.option(
    "--fuzzy-matching / --no-fuzzy-matching",
    show_default=True,
    default=True,
    help="Use fuzzy matching when merging .pot changes into .po files. "
    "Only applies when --msgmerge or --msgmerge-if-new-pot are passed.",
)
@click.option(
    "--purge-old-translations / --no-purge-old-translations",
    show_default=True,
    default=False,
    help="Remove comment lines containing old translations from .po files. "
    "Only applies when --msgmerge or --msgmerge-if-new-pot are passed.",
)
@click.option(
    "--commit / --no-commit",
    show_default=True,
    help="Git commit exported .pot files if needed.",
)
@click.option(
    "--commit-message", show_default=True, default="[UPD] Update {addon_name}.pot"
)
def main(
    env,
    addons_dir,
    modules,
    msgmerge,
    commit,
    msgmerge_if_new_pot,
    commit_message,
    fuzzy_matching,
    purge_old_translations,
):
    """Export translation (.pot) files of addons
    installed in the database and present in addons_dir.
    Check that existing .po file are syntactically correct.
    Optionally, run msgmerge on the existing .po files to keep
    them up to date. Commit changes to git, if any.
    """
    addon_names = [addon_name for addon_name, _, _ in manifest.find_addons(addons_dir)]
    if modules:
        modules = {m.strip() for m in modules.split(",")}
        not_existing_modules = modules - set(addon_names)
        if not_existing_modules:
            raise click.ClickException(
                "Module(s) was not found: " + ", ".join(not_existing_modules)
            )
        addon_names = [
            addon_name for addon_name in addon_names if addon_name in modules
        ]
    if addon_names:
        modules = env["ir.module.module"].search(
            [("state", "=", "installed"), ("name", "in", addon_names)]
        )
        for module in modules:
            export_pot(
                env,
                module,
                addons_dir,
                msgmerge,
                commit,
                msgmerge_if_new_pot,
                commit_message,
                fuzzy_matching,
                purge_old_translations,
            )


if __name__ == "__main__":
    main()
