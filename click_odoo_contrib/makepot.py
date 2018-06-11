# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64
import io
import os
import re
import subprocess

import click
import click_odoo

from . import manifest
from . import gitutils

LINE_PATTERNS_TO_REMOVE = [
    r'"POT-Creation-Date:.*?"[\n\r]',
    r'"PO-Revision-Date:.*?"[\n\r]',
]

PO_FILE_EXT = '.po'
POT_FILE_EXT = '.pot'


def export_pot(env, module, addons_dir, commit):
    addon_name = module.name
    addon_dir = os.path.join(addons_dir, addon_name)
    i18n_path = os.path.join(addon_dir, 'i18n')
    pot_filepath = os.path.join(i18n_path, addon_name + POT_FILE_EXT)

    lang_export = env['base.language.export'].create({
        'lang': '__new__',
        'format': 'po',
        'modules': [(6, 0, [module.id])]
    })
    lang_export.act_getfile()

    if not os.path.isdir(i18n_path):
        os.makedirs(i18n_path)

    module_languages = set()
    for filename in os.listdir(i18n_path):
        is_po_file = filename.endswith(PO_FILE_EXT)
        skip_file = (
            not is_po_file or
            not os.path.isfile(os.path.join(i18n_path, filename)))
        if skip_file:
            continue
        language = filename.replace(PO_FILE_EXT, '')
        module_languages.add(language)

    with io.open(pot_filepath, 'w', encoding='utf-8') as pot_file:
        file_content = base64.b64decode(lang_export.data).decode('utf-8')
        for pattern in LINE_PATTERNS_TO_REMOVE:
            file_content = re.sub(
                pattern, '', file_content, flags=re.MULTILINE)
        pot_file.write(file_content)

    for lang in module_languages:
        lang_filename = lang + PO_FILE_EXT
        lang_filepath = os.path.join(i18n_path, lang_filename)
        if not os.path.isfile(lang_filepath):
            with open(lang_filepath, 'w'):
                pass
        subprocess.check_call([
            'msgmerge',
            '--quiet',
            '-U',
            lang_filepath,
            pot_filepath,
        ])

    if commit:
        gitutils.commit_if_needed(
            [pot_filepath],
            "[UPD] {}.pot".format(addon_name),
            cwd=addons_dir,
        )
        gitutils.commit_if_needed(
            [i18n_path],
            "[UPD] {} {}.po".format(addon_name, '/'.join(module_languages)),
            cwd=addons_dir,
        )


@click.command()
@click_odoo.env_options(with_rollback=False, default_log_level='error')
@click.option('--addons-dir', default='.', show_default=True)
@click.option('--commit / --no-commit', show_default=True,
              help="Git commit exported .pot files if needed.")
def main(env, addons_dir, commit):
    """ Export translation (.pot) files of addons
    installed in the database and present in addons_dir.
    """
    addon_names = [
        addon_name
        for addon_name, _, _ in manifest.find_addons(addons_dir)
    ]
    if addon_names:
        modules = env['ir.module.module'].search([
            ('state', '=', 'installed'),
            ('name', 'in', addon_names),
        ])
        for module in modules:
            export_pot(env, module, addons_dir, commit)


if __name__ == '__main__':
    main()
