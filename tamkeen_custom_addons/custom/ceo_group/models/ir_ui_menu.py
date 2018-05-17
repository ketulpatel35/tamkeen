from odoo import fields, models


class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    appear_to_ceo = fields.Boolean('Appear To CEO')
