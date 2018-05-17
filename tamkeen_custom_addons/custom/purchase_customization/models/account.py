# -*- encoding: utf-8 -*-

from odoo import fields, api, models


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    po_company_number = fields.Char(string='PO Company Number')

    @api.model
    def default_get(self, fields_list):
        res = super(account_invoice, self).default_get(fields_list)
        if res.get('purchase_id'):
            purchase = self.env['purchase.order'].browse(
                res.get('purchase_id'))
            res.update({'po_company_number': purchase.po_company_number})
            res.update({'reference': purchase.partner_ref})
        return res
