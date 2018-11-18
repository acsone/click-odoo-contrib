try:
    from odoo import models, fields
except ImportError:
    from openerp import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"
    custom_field = fields.Char()
