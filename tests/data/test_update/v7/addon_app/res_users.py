from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"
    custom_field = fields.Char()
