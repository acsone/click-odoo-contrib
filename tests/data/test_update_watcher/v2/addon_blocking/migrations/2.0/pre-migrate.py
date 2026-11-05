def migrate(cr, version):
    # Keep an exclusive lock on res_partner for a while, like a long migration
    cr.execute("ALTER TABLE res_partner ADD COLUMN watcher_blocking_column INTEGER")
    cr.execute("SELECT pg_sleep(5)")
