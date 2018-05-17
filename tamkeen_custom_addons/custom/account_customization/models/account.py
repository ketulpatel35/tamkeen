# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    name_arabic = fields.Char(string='الأسم بالعربية')
    internal_type_id = fields.Many2one('account.internal.type',
                                       string='Internal Type')
    category_id = fields.Many2one('account.category', string='Category')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment = fields.Selection([
        ('cash', 'Cash'),
        ('banktransfer', 'Bank Transfer'),
        ('sadad', 'Sadad'),
        ('cheque', 'Cheque'),
    ], string='Payment')
    transaction_type = fields.Selection([
        ('payment', 'Payments'),
        ('advance', 'Advance'),
    ], string='Transaction Type ')
    cheque_number = fields.Char(string='Cheque Number')
    reference = fields.Char(string='Payment Reference')
    advance_account_id = fields.Many2one('account.account',
                                         string='Advance Account')
    note = fields.Char('Note')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountPayment, self)._onchange_partner_id()
        if self.partner_id:
            res['domain'] = {'payment_token_id': [('partner_id', '=',
                                                   self.partner_id.id),
                                                  ('acquirer_id.auto_confirm',
                                                   '!=', 'authorize')]}
            if self.payment_type == 'outbound':
                self.advance_account_id = \
                    self.partner_id.property_account_supplier_advance
            elif self.payment_type == 'inbound':
                self.advance_account_id = \
                    self.partner_id.property_account_customer_advance
        return res

    @api.multi
    def post(self):
        """
        Overwrite post method form addons
        Create the journal items for the payment and update the payment's
         state to 'posted'.
        A journal entry is created containing an item in the source liquidity
         account (selected journal's default_debit or default_credit)
        and another in the destination reconciliable account
        (see _compute_destination_account_id).
        If invoice_ids is not empty, there will be one reconciliable
         move line per invoice to reconcile with.
        If the payment is a transfer, a second journal entry is
         created in the destination journal to receive money from
         the transfer account.
        """
        res = super(AccountPayment, self).post()
        for rec in self:
            reference = rec.reference or self.env['ir.sequence'] \
                .next_by_code('account.payment')
            account_inv = self.env['account.invoice']
            if self._context.get('active_id'):
                active_rec = account_inv.browse(self._context.get('active_id'))
                if active_rec and active_rec.type == "in_invoice" and \
                        active_rec.origin and rec.communication:
                    rec.communication += ' - ' + str(active_rec.origin) or ''
            rec.write({'reference': reference})
        return res




class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    category_id = fields.Many2one('account.category', string='Category')


class AccountInternalType(models.Model):
    _name = "account.internal.type"
    _description = " Internal Type"

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, translate=True)
    account_ids = fields.One2many('account.account', 'internal_type_id',
                                  string='Account', readonly=True)


class AccountCategory(models.Model):
    _name = "account.category"
    _description = " Account Category"

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, translate=True)
    account_ids = fields.One2many('account.account', 'category_id',
                                  string='Account', readonly=True)
    analytic_account_ids = fields.One2many('account.analytic.account',
                                           'category_id',string='Analytic '
                                                                'Account', readonly=True)