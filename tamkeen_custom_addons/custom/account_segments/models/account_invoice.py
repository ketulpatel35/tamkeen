# -*- coding: utf-8 -*-
from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          track_visibility='onchange',
                                          string="Analytic Account")

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        value = res.get('type', False)
        if value == 'in_invoice':
            if res.get('purchase_id'):
                po = self.env['purchase.order'].browse(res.get('purchase_id'))
                if po:
                    res.update({'purchase_id': po.id})
                    if po.cost_centre_id:
                        res.update({'cost_centre_id': po.cost_centre_id.id})
                    if po.account_analytic_id:
                        res.update({'account_analytic_id':
                                        po.account_analytic_id.id})
        return res

    def _prepare_invoice_line_from_po_line(self, line):
        """
        :param line:
        :return:
        """
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        if line:
            if line.cost_centre_id:
                res.update({'cost_centre_id': line.cost_centre_id.id})
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
