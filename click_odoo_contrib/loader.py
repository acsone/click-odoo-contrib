#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 XOE Corp. SAS (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import contextlib
from datetime import datetime, timedelta
from fnmatch import fnmatch
import hashlib
import logging
import os
import re

import click
import click_odoo

from click_odoo import odoo

from .manifest import expand_dependencies

_logger = logging.getLogger(__name__)


@click.command()
@click_odoo.env_options(default_log_level='warn',
                        with_database=False,
                        with_rollback=False)
@click.option('--file', '-f', required=True,
              help="Path to the file, that you want to load. "
                   "You can specify this option multiple times "
                   "for more than one file to load.")
@click.option('--database', '-d', required=True,
              help="The database, into which to load the data.")
@click.option('--onchange/--no-onchange', default=True, show_default=True,
              help="Trigger onchange methods as if data was entered "
                   "through normal form views.")
@click.option('--batch', default=50, show_default=True,
              help="The batch size. Records are cut-off for iteration "
                   "after so many records. Nested lines do not count "
                   "towards that value. In *very* complex loading "
                   "scenarios: take some care with nested records.")
@click.option('--output/--no-output', default=True, show_default=True,
              help="Persist the server's output into a JSON database "
                   "alongside each source file. On subsequent runs, "
                   "sucessfull loads are deduplicated.")
def main(env, file, database, dbconninfo,
         onchange, batch, output):
    """ Load data into an Odoo Database.

    Loads data supplied in a supported format by file or stream
    into a local or remote Odoo database.

    Highlights:

    - Detects model-level graph dependency on related fields and
      record level graph dependencies in tree-like tables (hierarchies)
      and loads everything in the correct order.

    - Supported import formats are governed by the excellent pandas library.
      Most useful: JSON & CSV

    - Through `output` persistence flag: can be run idempotently.

    - Can trigger onchange as if data was entered through forms.

    Returns joy.
    """
