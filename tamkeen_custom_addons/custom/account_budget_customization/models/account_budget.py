from odoo import models, fields


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    product_id = fields.Many2one('product.product', string='Product')