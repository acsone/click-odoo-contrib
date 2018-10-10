# Copyright 2018 XOE Corp. SAS (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

from click.testing import CliRunner
# import mock

from click_odoo_contrib.loader import main

HERE = os.path.dirname(__file__)
DATADIR = os.path.join(HERE, 'data/test_loader/')


def test_read_files(odoodb, odoocfg):
    """ Test if XLSX, XLS, CSV & JSON files load into DataSetGraph """

    # First try if script bails out correctly for config errors
    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "noname1",
        '--src', DATADIR + "noname1",
        # default: '--type', "csv",
        'res.partner'
    ])

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xls",
        '--type', "xls",
        'res.partner'
    ])

    # Serious loadnig
    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xlsx",
        '--type', "xls",
    ])

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res_partner.xls",
        '--type', "xls",
    ])

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.partner.csv",
        # default: '--type', "csv",
    ])

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.partner.json",
        '--type', "json",
    ])

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "noname1",
        '--src', DATADIR + "noname1",
        # default: '--type', "csv",
        'res.partner res.partner'
    ])


def test_file_dependency(odoodb, odoocfg):
    """ Test if two dependend files will be loaded in the correct order """

    CliRunner().invoke(main, [
        '-d', odoodb,
        '-c', str(odoocfg),
        '--src', DATADIR + "res.country.state.json",  # Should load second
        '--src', DATADIR + "res.country.json",  # Should load first
        '--type', "json",
    ])
