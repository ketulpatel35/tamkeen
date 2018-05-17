# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, api, _
from odoo.exceptions import Warning


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_invoiced_qty(self, po_line, inv_line_rec):
        """
        get remaining quantity to be invoiced
        :param po_line: po line record
        :param inv_line_rec: invoice line record
        :return:
        """
        qty = 0.0
        for inv_line in po_line.invoice_lines:
            if inv_line.invoice_id.state not in ['cancel'] and \
                            inv_line_rec.id != inv_line.id:
                qty += inv_line.uom_id._compute_quantity(inv_line.quantity,
                                                         po_line.product_uom)
        rem_qty = po_line.product_qty - qty
        return rem_qty

    @api.multi
    def check_amount_validation(self, inv_line_rec):
        """
        check Allowed to Invoice more then the Purchase Order Amount
        :return:
        """
        rem_qty = self.get_invoiced_qty(inv_line_rec.purchase_line_id,
                                        inv_line_rec)
        if inv_line_rec.quantity > rem_qty:
            raise Warning(_('You are not allowed to invoice more '
                            'than the Purchase Order %s amount.') % (
                              inv_line_rec.purchase_id.name))
        if self.currency_id and self.currency_id.id == \
                inv_line_rec.purchase_id.currency_id.id:
            if inv_line_rec.price_unit > inv_line_rec.purchase_line_id.price_unit:
                raise Warning(_('You are not allowed to invoice more '
                                'than the Purchase Order %s amount.') % (
                                  inv_line_rec.purchase_id.name))
        else:
            price_unit = inv_line_rec.purchase_id.currency_id.compute(
                inv_line_rec.purchase_line_id.price_unit, self.currency_id,
                round=False)
            if round(inv_line_rec.price_unit) > round(price_unit):
                raise Warning(_('You are not allowed to invoice more '
                                'than the Purchase Order %s amount.') % (
                                  inv_line_rec.purchase_id.name))

    @api.multi
    def check_diff_currency_validation(self, inv_line_rec):
        """
        check validation
        - same currency for PO and Invoice
        :return:
        """
        if inv_line_rec.currency_id != inv_line_rec.purchase_id.currency_id:
            raise Warning(_(
                'You are not allowed to select a different currency which is'
                'not like the related purchase order.'))

    @api.multi
    def submit_to_first_validate(self):
        """
        submit to first validation
        :return:
        """
        for rec in self:
            # check invoice amount validation based on PO
            for inv_line_rec in rec.invoice_line_ids:
                if inv_line_rec.purchase_id:
                    # if not_allow_more_amount is true then have to check
                    # validation for invoice amount not grater then purchase
                    # order amount.
                    if not inv_line_rec.purchase_id.not_allow_more_amount:
                        rec.check_amount_validation(inv_line_rec)
                    # check for currency validation
                    if not inv_line_rec.purchase_id.not_allow_diff_currency:
                        rec.check_diff_currency_validation(inv_line_rec)
                        # check validation only ones.
        return super(AccountInvoice, self).submit_to_first_validate()
