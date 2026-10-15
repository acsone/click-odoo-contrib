from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Adding the column needs an exclusive lock on res_partner
    watcher_blocked_field = fields.Char()
