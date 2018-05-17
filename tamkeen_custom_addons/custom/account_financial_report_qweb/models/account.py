# -*- coding: utf-8 -*-
# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        help="If flagged, no details will be displayed in "
             "the General Ledger report (the webkit one only), "
             "only centralized amounts per period.")


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        label = ''
        for line in move_lines:
            invoice_id = self.browse(line[2].get('invoice_id'))
            result = filter(lambda each: each['name'] == invoice_id.name or '/', [line[2]])
            if result:
                # For Sale Order
                label = invoice_id.origin
                if invoice_id.journal_id.type == 'sale' and invoice_id.name:
                    label = label and label + ' : ' + invoice_id.name or invoice_id.name
                # For Purchase order
                if invoice_id.journal_id.type == 'purchase' and (invoice_id.reference or invoice_id.po_company_number):
                    label = label and label + ' : ' + invoice_id.reference or invoice_id.reference
                    label = invoice_id.po_company_number and label + ' : ' + invoice_id.po_company_number or label
                line[2].update({'name': label or invoice_id.number or '/'})
        return move_lines
