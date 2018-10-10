# Copyright 2018 XOE Corp. SAS (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta, datetime
import os
import subprocess
import sys
import textwrap

from click.testing import CliRunner
import mock
import pytest

import click_odoo
from click_odoo_contrib import loader
from click_odoo_contrib.loader import main

HERE = os.path.dirname(__file__)
DATADIR = os.path.join(HERE, 'data/test_loader/')

# @click.command()
# @click_odoo.env_options(default_log_level='warn', with_rollback=False)
# @click.option('--src', '-s', type=click.File('rb', lazy=True,exists=True),
#               multiple=True, required=True,
#               help="Path to the file, that you want to load. "
#                    "You can specify this option multiple times "
#                    "for more than one file to load.")
# @click.option('--type', '-t', type=click.Choice(['json', 'csv', 'xls']),
#               show_default=True, default='csv', help="Input date type.")
# @click.option('--onchange/--no-onchange', default=True, show_default=True,
#               help="Trigger onchange methods as if data was entered "
#                    "through normal form views.")
# @click.option('--batch', default=50, show_default=True,
#               help="The batch size. Records are cut-off for iteration "
#                    "after so many records. Nested lines do not count "
#                    "towards that value. In *very* complex loading "
#                    "scenarios: take some care with nested records.")
# @click.option('--out', type=click.File('wb', lazy=True),
#               default="./log.json", show_default=True,
#               help="Persist the server's output into a JSON database "
#                    "alongside each source file. On subsequent runs, "
#                    "sucessfull loads are deduplicated.")
# @click.argument('models', required=False, nargs=-1,
#               help="When loading from unnamed streams, you can specify "
#                    "the modles of each stream. They must be presented "
#                    "in the same order as the streams. Note: don't use "
#                    "with xls streams as model is inferred from sheetnames.")

def test_read_files(odoodb, odoocfg):
    """ Test if XLSX, XLS, CSV & JSON files load correctly into DataSetGraph """

    # First try if script bails out correctly for config errors

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "noname1",
        '--src', DATADIR + "noname1",
        # default: '--type', "csv",
        'res.partner'
    ])

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xls",
        '--type', "xls",
        'res.partner'
    ])

    # Serious loadnig

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xlsx",
        '--type', "xls",
    ])


    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xls",
        '--type', "xls",
    ])


    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.partner.csv",
        # default: '--type', "csv",
    ])

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.partner.json",
        '--type', "json",
    ])


    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "noname1",
        '--src', DATADIR + "noname1",
        # default: '--type', "csv",
        'res.partner res.partner'
    ])


def test_file_dependency(odoodb, odoocfg):
    """ Test if two interdependend files will be loaded in the correct order """

    result = CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.country.state.json",  # Should end up being loaded second
        '--src', DATADIR + "res.country.json",  # Should end up being loaded first
        '--type', "json",
    ])
