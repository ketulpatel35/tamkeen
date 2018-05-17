# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account')

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(grouped=False,
                                                           final=False)
        invoice_obj = self.env['account.invoice']
        for inv in res:
            invoice_rec = invoice_obj.browse(inv)
            invoice_rec.write({
                'cost_centre_id': self.cost_centre_id.id,
                'account_analytic_id': self.account_analytic_id \
                    and self.account_analytic_id.id or False
            })
            for inv_line_rec in invoice_rec.invoice_line_ids:
                inv_line_rec.write({
                    'cost_centre_id': self.cost_centre_id.id,
                    'account_analytic_id': 
                self.account_analytic_id \
                        and self.account_analytic_id or False
                })
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")

    @api.model
    def default_get(self, fields_list):
        res = super(SaleOrderLine, self).default_get(fields_list)
        if self._context:
            if self._context.get('cost_centre_id'):
                res.update({
                    'cost_centre_id': self._context.get('cost_centre_id')
                })
        return res
