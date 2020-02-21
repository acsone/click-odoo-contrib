# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import hashlib
from contextlib import contextmanager

from click_odoo import odoo


@contextmanager
def pg_connect():
    conn = odoo.sql_db.db_connect("postgres")
    cr = conn.cursor()
    cr.autocommit(True)
    try:
        yield cr._obj
    finally:
        cr.close()


def db_exists(dbname):
    with pg_connect() as cr:
        cr.execute(
            "SELECT datname FROM pg_catalog.pg_database "
            "WHERE lower(datname) = lower(%s)",
            (dbname,),
        )
        return bool(cr.fetchone())


def terminate_connections(dbname):
    with pg_connect() as cr:
        cr.execute(
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "
            "FROM pg_stat_activity "
            "WHERE pg_stat_activity.datname = %s "
            "AND pid <> pg_backend_pid();",
            (dbname,),
        )


@contextmanager
def db_management_enabled():
    list_db = odoo.tools.config["list_db"]
    odoo.tools.config["list_db"] = True
    try:
        yield
    finally:
        odoo.tools.config["list_db"] = list_db


@contextmanager
def advisory_lock(cr, name):
    # try to make a unique lock id based on a string
    h = hashlib.sha1()
    h.update(name.encode("utf8"))
    lock_id = int(h.hexdigest()[:14], 16)
    cr.execute("SELECT pg_advisory_lock(%s::bigint)", (lock_id,))
    try:
        yield
    finally:
        cr.execute("SELECT pg_advisory_unlock(%s::bigint)", (lock_id,))
