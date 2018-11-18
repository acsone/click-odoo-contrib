def migrate(cr, version):
    cr.execute("UPDATE ir_module_module SET state='to remove' WHERE name='addon_d2'")

