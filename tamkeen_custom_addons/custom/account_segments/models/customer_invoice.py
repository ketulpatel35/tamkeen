# -*- coding: utf-8 -*-
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")

    @api.onchange('cost_centre_id', 'account_analytic_id')
    def _inv_onchange_cost_center(self):
        """
        :return:
        """
        if self.cost_centre_id:
            for inv_line in self.invoice_line_ids:
                if not inv_line.cost_centre_id:
                    inv_line.cost_centre_id = self.cost_centre_id.id
        if self.account_analytic_id:
            for inv_line in self.invoice_line_ids:
                if not inv_line.account_analytic_id:
                    inv_line.account_analytic_id = self.account_analytic_id.id


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoiceLine, self).default_get(fields_list)
        if self._context:
            if self._context.get('cost_centre_id'):
                res.update({
                    'cost_centre_id': self._context.get('cost_centre_id')
                })
        return res
