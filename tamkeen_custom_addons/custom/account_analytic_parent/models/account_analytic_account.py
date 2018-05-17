# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    parent_id = fields.Many2one(
        'account.analytic.account',
        string='Parent Analytic Account'
    )
    child_ids = fields.One2many('account.analytic.account', 'parent_id',
                                'Child Accounts', copy=True)

    @api.multi
    def _compute_debit_credit_balance(self):
        """
        Warning, this method overwrites the standard because the hierarchy
        of analytic account changes
        """
        super(AccountAnalyticAccount, self)._compute_debit_credit_balance()
        for account in self:
            account.debit = sum([child.debit for child in self.search(
                [('id', 'child_of', account.id)])])
            account.credit = sum([child.credit for child in self.search(
                [('id', 'child_of', account.id)])])
            account.balance = sum([child.balance for child in self.search(
                [('id', 'child_of', account.id)])])

    @api.multi
    @api.constrains('parent_id')
    def check_recursion(self):
        for account in self:
            if not super(AccountAnalyticAccount, account)._check_recursion():
                raise UserError(
                    _('You can not create recursive analytic accounts.'),
                )

    @api.multi
    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for account in self:
            account.partner_id = account.parent_id.partner_id

    @api.multi
    def name_get(self):
        res = []
        for account in self:
            current = account
            name = "[" + tools.ustr(current.code or '') + "]" + tools.ustr(current.name)
            while current.parent_id:
                parent_name = "[" + tools.ustr(current.parent_id.code) + "]" + tools.ustr(current.parent_id.name)
                name = '%s / %s' % (parent_name, name)
                current = current.parent_id
            res.append((account.id, name))
        return res
