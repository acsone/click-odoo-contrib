# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import hashlib
import os
import warnings
from contextlib import contextmanager

from click_odoo import OdooEnvironment, odoo


@contextmanager
def pg_connect():
    conn = odoo.sql_db.db_connect("postgres")
    cr = conn.cursor()
    if odoo.release.version_info > (16, 0):
        cr._cnx.autocommit = True
    else:
        # We are not going to use the ORM with this connection
        # so silence the Odoo warning about autocommit.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
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
    old_params = {"list_db": odoo.tools.config["list_db"]}
    odoo.tools.config["list_db"] = True
    # Work around odoo.service.db.list_dbs() not finding the database
    # when postgres connection info is passed as PG* environment
    # variables.
    if odoo.release.version_info < (12, 0):
        for v in ("host", "port", "user", "password"):
            odoov = "db_" + v.lower()
            pgv = "PG" + v.upper()
            if not odoo.tools.config[odoov] and pgv in os.environ:
                old_params[odoov] = odoo.tools.config[odoov]
                odoo.tools.config[odoov] = os.environ[pgv]
    try:
        yield
    finally:
        for key, value in old_params.items():
            odoo.tools.config[key] = value


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


def reset_config_parameters(dbname):
    """
    Reset config parameters to default value. This is useful to avoid
    conflicts between databases on copy or restore
    (dbuuid, ...)
    """
    with OdooEnvironment(dbname) as env:
        env["ir.config_parameter"].init(force=True)

        # reset enterprise keys if exists
        env.cr.execute(
            """
        DELETE FROM ir_config_parameter
        WHERE key = 'database.enterprise_code';

        UPDATE ir_config_parameter
        SET value = 'copy'
        WHERE key = 'database.expiration_reason'
        AND value != 'demo';

        UPDATE ir_config_parameter
        SET value = CURRENT_DATE + INTERVAL '2 month'
        WHERE key = 'database.expiration_date';

        """
        )
