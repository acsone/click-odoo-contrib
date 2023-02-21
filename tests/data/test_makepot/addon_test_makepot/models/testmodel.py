from odoo import models, fields


class TestModel(models.Model):

    _name = "test.model"

    myfield = fields.Char()
