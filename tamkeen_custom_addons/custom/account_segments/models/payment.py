# -*- coding: utf-8 -*-
from openerp import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')