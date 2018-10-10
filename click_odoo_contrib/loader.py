#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 XOE Corp. SAS (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import contextlib
from datetime import datetime, timedelta
from fnmatch import fnmatch
import hashlib
import logging
import pandas as pd
import networkx as nx
import os
import re

import click
import click_odoo

from click_odoo import odoo

from .manifest import expand_dependencies

_logger = logging.getLogger(__name__)

class DataSetGraph(nx.DiGraph):

    def load_metadata(self):
        """ Loads all required metadata from the odoo enviornment
        for all nodes in the graph and normalizes column names"""
        for node in self.nodes:
            # Normalize column names
            node['cols'] = []
            for col in node['df'].columns:
                node['cols'].append({'name': col.rstrip('/.id').rstrip('/id')})

            # TODO: Get info from `ctx.env`
            node['fields'] = {'stored': [], 'relational': [{'name':'', 'model':''}]}
            node['parent'] = 'parent_id'
            node['repr'] = ''

            # Enrich cols with data from odoo env (convenience)
            for col in node['cols']:
                for rel in node['fields']['relational'].items():
                    if col['name'] == rel['name']:
                        col['model'] = rel['model']

    def seed_edges(self):
        """ Seeds the edges based on the df columns relations
        and existing models in the graph """
        for node_u, cols in self.nodes(data='fields'):
            for col in cols:
                for node_v, model in self.nodes(data='model').items():
                    if col['model'] != model:
                        self.add_edge(node_u, node_v, column=col['name'])

    def order_to_parent(self):
        """ Reorganizes dataframes so they are in suitable loading
        order if a parent field is present.
        TODO: Does not work with nested rows. Flatten everything first? """
        for node, parent in self.nodes(data='parent'):
            if parent not in [c['name'] for c in node['cols'].items()]:
                continue
            recordGraph = nx.DiGraph()
            recordGraph.add_nodes_from(node['df'].index.tolist())
            recordGraph.add_edges_from(
                node['df'].loc[:,parent][node['df'][parent].notnull()].itertuples)
            node['df'].reindex(nx.topological_sort(recordGraph.reverse(False)))





GRAPH = DataSetGraph()

def _infer_valid_model(filename):
    """ Returns a valid model name from filename or False
    Filenames are expected to convey the model
    just as Odoo does when loading csv files. """

    # TODO: validate model against `ctx.env`
    return 'accout.accoount' or False

def _load_dataframes(filepath):
    """ Loads dataframes into DataSetGraph global receiver """

    # Special case: Excle file with sheets
    if filepath.endswith('.xls') or \
        filepath.endswith('.xlsx'):
        xlf = pd.ExcelFile(filepath)
        for name in xlf.sheet_names:
            model = _infer_valid_model(name)
            if not model:
                continue
            df = _read_excel(xlf, name)
            GRAPH.add_node(model=model, df=df)
        return

    filename = os.path.basename(filepath)
    model = _infer_valid_model(filename)
    if not model:
        return
    if filepath.endswith('.csv'):
        df = _read_csv(filepath)
    if filepath.endswith('.json'):
        df = _read_json(filepath)
    GRAPH.add_node(model=model, df=df)

def _read_csv(filepath_or_buffer):
    """ Reads a CSV file through pandas from a buffer.
    Returns a DataFrame. """
    return pd.read_csv(filepath_or_buffer)

def _read_json(filepath_or_buffer):
    """ Reads a JSON file through pandas from a buffer.
    Returns a DataFrame. """
    return pd.read_json(filepath_or_buffer)

def _read_excel(excelfile, sheetname):
    """ Reads a XLS/XLSX file through pandas from an ExcelFile object.
    Returns a DataFrame. """
    return pd.read_excel(excelfile, sheetname)




@click.command()
@click_odoo.env_options(default_log_level='warn',
                        with_database=False,
                        with_rollback=False)
@click.option('--file', '-f', required=True,
              help="Path to the file, that you want to load. "
                   "You can specify this option multiple times "
                   "for more than one file to load.")
@click.option('--stream-json', required=True,
              help="Instead of a file, recieves a single, JSON-typed, stream.")
@click.option('--stream-csv', required=True,
              help="Instead of a file, recieves a single, CSV-typed, stream.")
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
