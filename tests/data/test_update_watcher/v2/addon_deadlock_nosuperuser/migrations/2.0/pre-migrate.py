def migrate(cr, version):
    # Lock two tables in a row, like Odoo dropping NOT NULL constraints in the
    # tables of several models while it loads a module
    cr.execute(
        "ALTER TABLE res_partner "
        "ADD COLUMN watcher_deadlock_nosuperuser_partner INTEGER"
    )
    cr.execute(
        "ALTER TABLE res_company "
        "ADD COLUMN watcher_deadlock_nosuperuser_company INTEGER"
    )
