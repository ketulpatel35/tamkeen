# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from calendar import monthrange


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    prepayment = fields.Boolean('Is PrePayment')
    prepayment_type_id = fields.Many2one('account.prepayment.type', 'PrePayment Type')

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        prepayment_obj = self.env['account.prepayment']
        company_currency = self.env.user.company_id.currency_id
        for rec in self:
            prepayment_recs = prepayment_obj.search([('invoice_id', '=', rec.id)])
            if rec.prepayment and rec.prepayment_type_id and not prepayment_recs:
                no_of_lines = rec.prepayment_type_id.no_of_entries
                month_gap = rec.prepayment_type_id.months
                inv_currency = rec.currency_id
                for line in rec.invoice_line_ids:
                    amount = float(line.quantity * line.price_unit)
                    if company_currency.id != inv_currency.id:
                        amount = inv_currency.compute(amount,
                                                      company_currency,
                                                      round=True)
                    prepayment_rec = prepayment_obj.create({
                        'prepayment_type_id': rec.prepayment_type_id.id,
                        'date': rec.date_invoice,
                        'start_date': rec.date_invoice,
                        'invoice_id': rec.id,
                        'no_of_entries': rec.prepayment_type_id.no_of_entries,
                        'months': rec.prepayment_type_id.months,
                        'value': amount,
                        'account_analytic_id': line.account_analytic_id and
                        line.account_analytic_id.id or False,
                        'no_of_entries': no_of_lines,
                        'months': month_gap,
                        'entry_account_id': 
                        rec.prepayment_type_id.entry_account_id and
                        rec.prepayment_type_id.entry_account_id.id or False,
                        'account_id': rec.prepayment_type_id.account_id and 
                        rec.prepayment_type_id.account_id.id or False,
                        'reference': rec.origin,
                        'partner_id': rec.partner_id.id,
                        'product_id': line.product_id and line.product_id.id or False,
                        'partner_reference': rec.reference
                    })
                    prepayment_rec.generate_schedule()
        return res

    @api.onchange('prepayment', 'prepayment_type_id')
    def onchange_prepayment(self):
        context = dict(self._context) or {}
        res = {'value': {}}
        line_obj = self.env['account.invoice.line']
        if not self.prepayment:
            self.prepayment_type_id = False
        else:
            if self.prepayment_type_id and \
                    self.prepayment_type_id.prepaid_account_id:
                account_id = self.prepayment_type_id.prepaid_account_id.id
                for line in context.get('lines', []):
                    if line and line[0] == 4:
                        line_rec = line_obj.browse(line[1])
                        line_rec.write({'account_id': account_id})
                    elif line[0] == 0:
                        line[2].update({'account_id': account_id})
                res['value']['invoice_line_ids'] = context.get('lines')
        return res

    @api.multi
    def action_invoice_cancel(self):
        prepayment_obj = self.env['account.prepayment']
        for rec in self:
            prepayment_recs = prepayment_obj.search([('invoice_id', '=', rec.id), ('state', 'not in', ['draft'])])
            if prepayment_recs:
                prepayment_names = [prepayment.name for prepayment in prepayment_recs]
                prepayment_names = '\n'.join(map(str, prepayment_names))
                raise ValidationError(_('You must set below prepayments to draft before cancelling invoice!\n%s' % prepayment_names))
        return super(AccountInvoice, self).action_invoice_cancel()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.v8
    def get_invoice_line_account(self, type, product, fpos, company):
        res = super(AccountInvoiceLine, self).\
            get_invoice_line_account(type, product, fpos, company)
        if self.invoice_id and self.invoice_id.prepayment and\
            self.product_id and \
                self.invoice_id.prepayment_type_id:
            self.invoice_id.prepayment_type_id and \
                self.invoice_id.prepayment_type_id.prepaid_account_id
        return res

