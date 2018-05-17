# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}


class AccountRegisterPayment(models.TransientModel):
    _inherit = 'account.register.payments'

    def _compute_total_invoices_amount(self, invoices):
        """ Compute the sum of the residual of invoices, expressed in the
        payment currency"""
        payment_currency = \
            self.currency_id or self.journal_id.currency_id or \
            self.journal_id.company_id.currency_id

        if all(inv.currency_id == payment_currency for inv in invoices):
            total = sum(invoices.mapped('residual_signed'))
        else:
            total = 0
            for inv in invoices:
                if inv.company_currency_id != payment_currency:
                    total += inv.company_currency_id.with_context(
                        date=self.payment_date).compute(
                        inv.residual_company_signed, payment_currency)
                else:
                    total += inv.residual_company_signed
        return abs(total)

    @api.one
    # @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    @api.depends('amount', 'journal_id')
    def _compute_payment_difference(self):
        self._context.get('active_ids')
        if len(self._context.get('active_ids')) == 0:
            return
        invoice_rec = self.env['account.invoice'].browse(self._context.get(
            'active_ids'))
        total = self._compute_total_invoices_amount(invoice_rec)
        if invoice_rec[0].type in ['in_invoice', 'out_refund']:
            self.payment_difference = self.amount - total
        else:
            self.payment_difference = total - self.amount

    payment_difference = fields.Monetary(readonly=True,
                                         compute='_compute_payment_difference')
    payment_difference_handling = fields.Selection(
        [('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')],
        default='open', string="Payment Difference", copy=False)
    writeoff_account_id = fields.Many2one('account.account',
                                          string="Difference Account",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)

    def get_payment_vals(self):
        """ Hook for extension """
        rec = super(AccountRegisterPayment, self).get_payment_vals()
        if rec:
            rec.update({
                'payment_difference_handling':
                    self.payment_difference_handling,
                'writeoff_account_id': self.writeoff_account_id.id,
            })
        return rec
