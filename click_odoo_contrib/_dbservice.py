# Copyright 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

"""Compatibility layer over Odoo's database management helpers.

Up to Odoo 19 these helpers lived in ``odoo.service.db``. Odoo 20 moved them
to ``odoo.modules.db``, renamed several of them, made some arguments
keyword-only, and dropped ``list_db_incompatible`` altogether. This module
exposes the subset used by click-odoo-contrib under names that are stable
across all supported series.
"""

from contextlib import closing

from click_odoo import odoo

__all__ = [
    "create_empty_database",
    "drop_db",
    "dump_db_manifest",
    "list_db_incompatible",
    "list_dbs",
    "restore_db",
]


if odoo.release.version_info >= (20, 0):
    import odoo.modules.db as _db
    import odoo.tools.sql

    create_empty_database = _db._create_empty_database
    dump_db_manifest = _db._dump_db_manifest
    list_dbs = _db.list_dbs
    drop_db = _db.drop

    def restore_db(db_name, dump_file, copy=False, neutralize_database=False):
        _db.restore(
            db_name,
            dump_file,
            copy=copy,
            neutralize_database=neutralize_database,
        )

    def list_db_incompatible(databases):
        """Return the databases that are not compatible with this Odoo version.

        Odoo 20 removed this helper without providing a replacement, so this
        is a port of the Odoo 19 implementation.
        """
        incompatible_databases = []
        server_version = ".".join(str(v) for v in odoo.release.version_info[:2])
        for database_name in databases:
            with closing(odoo.sql_db.db_connect(database_name).cursor()) as cr:
                if not odoo.tools.sql.table_exists(cr, "ir_module_module"):
                    incompatible_databases.append(database_name)
                    continue
                cr.execute(
                    "SELECT latest_version FROM ir_module_module WHERE name=%s",
                    ("base",),
                )
                base_version = cr.fetchone()
                if not base_version or not base_version[0]:
                    incompatible_databases.append(database_name)
                else:
                    # e.g. 10.saas~15
                    local_version = ".".join(base_version[0].split(".")[:2])
                    if local_version != server_version:
                        incompatible_databases.append(database_name)
        for database_name in incompatible_databases:
            # release connection
            odoo.sql_db.close_db(database_name)
        return incompatible_databases

else:
    import odoo.service.db as _db

    create_empty_database = _db._create_empty_database
    dump_db_manifest = _db.dump_db_manifest
    list_dbs = _db.list_dbs
    list_db_incompatible = _db.list_db_incompatible
    drop_db = _db.exp_drop

    def restore_db(db_name, dump_file, copy=False, neutralize_database=False):
        extra_kwargs = {}
        if odoo.release.version_info >= (16, 0):
            extra_kwargs["neutralize_database"] = neutralize_database
        _db.restore_db(db_name, dump_file, copy, **extra_kwargs)
