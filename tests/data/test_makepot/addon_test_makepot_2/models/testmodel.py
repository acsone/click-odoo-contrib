from odoo import models, fields


class TestModel2(models.Model):

    _name = "test.model2"

    myfield = fields.Char()
