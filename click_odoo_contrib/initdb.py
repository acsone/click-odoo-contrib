#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
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


EXCLUDE_PATTERNS = ('*.pyc', '*.pyo')


def check_dbname(dbname):
    if not re.match('^[A-Za-z][A-Za-z0-9-]*$', dbname):
        raise click.ClickException(
            "Invalid database name '{}'".format(dbname))


def check_cache_prefix(cache_prefix):
    if not re.match('^[A-Za-z][A-Za-z0-9-]{0,7}$', cache_prefix):
        raise click.ClickException(
            "Invalid cache prefix name '{}'".format(cache_prefix))


def odoo_createdb(dbname, demo, module_names):
    odoo.service.db._create_empty_database(dbname)
    odoo.tools.config['init'] = dict.fromkeys(module_names, 1)
    odoo.tools.config['without_demo'] = not demo
    if odoo.release.version_info[0] < 10:
        Registry = odoo.modules.registry.RegistryManager
    else:
        Registry = odoo.modules.registry.Registry
    Registry.new(dbname, force_demo=demo, update_module=True)
    _logger.info(click.style(
        "Created new Odoo database {dbname}.".format(**locals()),
        fg='green',
    ))
    odoo.sql_db.close_db(dbname)


def _fnmatch(filename, patterns):
    for pattern in patterns:
        if fnmatch(filename, pattern):
            return True
    return False


def _walk(top, exclude_patterns=EXCLUDE_PATTERNS):
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames.sort()
        reldir = os.path.relpath(dirpath, top)
        if reldir == '.':
            reldir = ''
        for filename in sorted(filenames):
            filepath = os.path.join(reldir, filename)
            if _fnmatch(filepath, exclude_patterns):
                continue
            yield filepath


def addons_hash(module_names, with_demo):
    h = hashlib.sha1()
    h.update('!demo={}!'.format(int(bool(with_demo))).encode('utf8'))
    for module_name in sorted(expand_dependencies(module_names, True)):
        module_path = odoo.modules.get_module_path(module_name)
        h.update(module_name.encode('utf8'))
        for filepath in _walk(module_path):
            h.update(filepath.encode('utf8'))
            with open(os.path.join(module_path, filepath), 'rb') as f:
                h.update(f.read())
    return h.hexdigest()


class DbCache:
    """ Manage a cache of db templates.

    Templates are named prefix-YYYYMMDD-hashsum, where
    YYYYMMDD is the date when the given hashsum has last been
    used for that prefix.
    """

    HASH_SIZE = hashlib.sha1().digest_size * 2
    MAX_HASHSUM = 'f' * HASH_SIZE

    def __init__(self, prefix):
        check_cache_prefix(prefix)
        self.prefix = prefix
        self.lock_id = self._make_lock_id()
        conn = odoo.sql_db.db_connect('postgres')
        self.pgcr = conn.cursor()
        self.pgcr.autocommit(True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.pgcr.close()

    def _make_lock_id(self):
        # try to make a unique lock id based on the cache prefix
        h = hashlib.sha1()
        h.update(self.prefix.encode('utf8'))
        return int(h.hexdigest()[:14], 16)

    @contextlib.contextmanager
    def _lock(self):
        self.pgcr.execute(
            "SELECT pg_advisory_lock(%s::bigint)",
            (self.lock_id,),
        )
        try:
            yield
        finally:
            self.pgcr.execute(
                "SELECT pg_advisory_unlock(%s::bigint)",
                (self.lock_id,),
            )

    def _make_pattern(self, dt=None, hs=None):
        if dt:
            dtpart = dt.strftime("%Y%m%d%H%M")
        else:
            dtpart = '_' * 12
        if hs:
            hspart = hs
        else:
            hspart = '_' * self.HASH_SIZE
        pattern = self.prefix + '-' + dtpart + '-' + hspart
        # 63 is max postgres db name, so we may truncate the hash part
        return pattern[:63]

    def _make_new_template_name(self, hashsum):
        return self._make_pattern(dt=datetime.utcnow(), hs=hashsum)

    def _create_db_from_template(self, dbname, template):
        _logger.info(click.style(
            "Creating database {dbname} "
            "from template {template}".format(**locals()),
            fg='green',
        ))
        self.pgcr.execute("""
            CREATE DATABASE "{dbname}"
            ENCODING 'unicode'
            TEMPLATE "{template}"
        """.format(**locals()))

    def _rename_db(self, dbname_from, dbname_to):
        self.pgcr.execute("""
            ALTER DATABASE "{dbname_from}"
            RENAME TO "{dbname_to}"
        """.format(**locals()))

    def _drop_db(self, dbname):
        _logger.info("Dropping database {dbname}".format(**locals()))
        self.pgcr.execute("""
            DROP DATABASE "{dbname}"
        """.format(**locals()))

    def _find_template(self, hashsum):
        """ search same prefix and hashsum, any date """
        pattern = self.prefix + '-____________-' + hashsum
        self.pgcr.execute("""
            SELECT datname FROM pg_database
            WHERE datname like %s
            ORDER BY datname DESC  -- MRU first
        """, (pattern, ))
        r = self.pgcr.fetchone()
        if r:
            return r[0]
        else:
            return None

    def create(self, new_database, hashsum):
        """ Create a new database from a cached template matching hashsum """
        with self._lock():
            template_name = self._find_template(hashsum)
            if not template_name:
                return False
            else:
                self._create_db_from_template(new_database, template_name)
                # change the template data (MRU mechanism)
                new_template_name = self._make_new_template_name(hashsum)
                if template_name != new_template_name:
                    self._rename_db(template_name, new_template_name)
                return True

    def add(self, new_database, hashsum):
        """ Create a new cached template """
        with self._lock():
            new_template_name = self._make_new_template_name(hashsum)
            self._create_db_from_template(new_template_name, new_database)

    @property
    def size(self):
        with self._lock():
            pattern = self._make_pattern()
            self.pgcr.execute("""
                SELECT count(*) FROM pg_database
                WHERE datname like %s
            """, (pattern, ))
            return self.pgcr.fetchone()[0]

    def purge(self):
        with self._lock():
            pattern = self._make_pattern()
            self.pgcr.execute("""
                SELECT datname FROM pg_database
                WHERE datname like %s
            """, (pattern, ))
            for datname, in self.pgcr.fetchall():
                self._drop_db(datname)

    def trim_size(self, max_size):
        with self._lock():
            pattern = self._make_pattern()
            self.pgcr.execute("""
                SELECT datname FROM pg_database
                WHERE datname like %s
                ORDER BY datname DESC
                OFFSET %s
            """, (pattern, max_size))
            for datname, in self.pgcr.fetchall():
                self._drop_db(datname)

    def trim_age(self, max_age):
        with self._lock():
            pattern = self._make_pattern()
            max_name = self._make_pattern(
                dt=datetime.utcnow() - max_age,
                hs=self.MAX_HASHSUM,
            )
            self.pgcr.execute("""
                SELECT datname FROM pg_database
                WHERE datname like %s
                  AND datname <= %s
                ORDER BY datname DESC
            """, (pattern, max_name))
            for datname, in self.pgcr.fetchall():
                self._drop_db(datname)


@click.command()
@click_odoo.env_options(default_log_level='warn',
                        with_database=False,
                        with_rollback=False)
@click.option('--new-database', '-n', required=False,
              help="Name of new database to create, possibly from cache. "
                   "If absent, only the cache trimming operation is executed.")
@click.option('--modules', '-m', default='base', show_default=True,
              help="Comma separated list of addons to install.")
@click.option('--demo/--no-demo', default=True, show_default=True,
              help="Load Odoo demo data.")
@click.option('--cache/--no-cache', default=True, show_default=True,
              help="Use a cache of database templates with the exact "
                   "same addons installed. Disabling this option "
                   "also disables all other cache-related operations "
                   "such as max-age or size.")
@click.option('--cache-prefix', default='cache', show_default=True,
              help="Prefix to use when naming cache template databases "
                   "(max 8 characters). CAUTION: all databases named like "
                   "{prefix}-____________-% will eventually be dropped "
                   "by the cache control mechanism, so choose the "
                   "prefix wisely.")
@click.option('--cache-max-age', default=30, show_default=True,
              type=int,
              help="Drop cache templates that have not been used for "
                   "more than N days. Use -1 to disable.")
@click.option('--cache-max-size', default=5, show_default=True,
              type=int,
              help="Keep N most recently used cache templates. Use "
                   "-1 to disable. Use 0 to empty cache.")
def main(env, new_database, modules, demo,
         cache, cache_prefix, cache_max_age, cache_max_size):
    """ Create an Odoo database with pre-installed modules.

    Almost like standard Odoo does with the -i option,
    except this script manages a cache of database templates with
    the exact same addons installed. This is particularly useful to
    save time when initializing test databases.

    Cached templates are identified by computing a sha1
    checksum of modules provided with the -m option, including their
    dependencies and corresponding auto_install modules.
    """
    if new_database:
        check_dbname(new_database)
    module_names = [m.strip() for m in modules.split(',')]
    if not cache:
        if new_database:
            odoo_createdb(new_database, demo, module_names)
        else:
            _logger.info(
                "Cache disabled and no new database name provided. "
                "Nothing to do."
            )
    else:
        with DbCache(cache_prefix) as dbcache:
            if new_database:
                hashsum = addons_hash(module_names, demo)
                if dbcache.create(new_database, hashsum):
                    _logger.info(click.style(
                        "Found matching database template! ✨ 🍰 ✨",
                        fg='green', bold=True,
                    ))
                else:
                    odoo_createdb(new_database, demo, module_names)
                    dbcache.add(new_database, hashsum)
            if cache_max_size >= 0:
                dbcache.trim_size(cache_max_size)
            if cache_max_age >= 0:
                dbcache.trim_age(timedelta(days=cache_max_age))


if __name__ == '__main__':  # pragma: no cover
    main()
