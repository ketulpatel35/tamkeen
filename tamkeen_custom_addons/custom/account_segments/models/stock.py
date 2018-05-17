# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')


class StockMove(models.Model):
    _inherit = "stock.move"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')