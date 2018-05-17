# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        """
        write some fields value in invoice
        :param order:
        :param so_line:
        :param amount:
        :return:
        """
        res = super(SaleAdvancePaymentInv, self)._create_invoice(
            order, so_line, amount)
        for invoice_rec in res:
            invoice_rec.write({
                'cost_centre_id': order.cost_centre_id.id,
            })
            for inv_line_rec in invoice_rec.invoice_line_ids:
                inv_line_rec.write({
                    'cost_centre_id': order.cost_centre_id.id,
                })
        return res


class account_payment(models.Model):
    _inherit = "account.payment"

    def _create_payment_entry(self, amount):
        """
        :param amount:
        :return:
        """
        res = super(account_payment, self)._create_payment_entry(amount)
        if self._context:
            if self._context.get('active_model') == 'account.invoice' and \
                    self._context.get('active_id'):
                acc_inv_recs = self.env['account.invoice'].browse(
                    self._context.get('active_ids'))
                for acc_inv_rec in acc_inv_recs:
                    for move_rec in res:
                        move_rec.write({
                            'cost_centre_id': acc_inv_rec.cost_centre_id.id,
                        })
                        for line_rec in move_rec.line_ids:
                            line_rec.write({
                                'cost_centre_id': acc_inv_rec.cost_centre_id.id
                            })
        return res


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        ctx_vals = {
            'cost_centre_id': self.cost_centre_id and self.cost_centre_id.id or False,
            'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False
        }
        self = self.with_context({'segment_vals': ctx_vals})
        return super(AccountInvoice, self).action_move_create()
