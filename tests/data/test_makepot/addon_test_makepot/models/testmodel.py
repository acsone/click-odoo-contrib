try:
    from odoo import models, fields
except ImportError:
    from openerp import models, fields


class TestModel(models.Model):

    _name = "test.model"

    myfield = fields.Char()
