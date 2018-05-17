# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    disposal_account_id = fields.Many2one('account.account', 'Disposal Account')
    disposal_journal_id = fields.Many2one('account.journal', 'Disposal Journal')


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    disposal_account_id = fields.Many2one('account.account', 'Disposal Account')
    disposal_journal_id = fields.Many2one('account.journal', 'Disposal Journal')
    disposal_type = fields.Selection([('write_off', 'Write Off'),
                                      ('sale', 'Sale')], 'Disposal Type', default='write_off')
    disposal_date = fields.Date('Disposal Date')
    disposal_amount = fields.Float('Disposal Amount')
    disposal_customer_id = fields.Many2one('res.partner', 'Disposal Customer')

    @api.onchange('category_id')
    def onchange_category_for_disposal_id(self):
        self.disposal_account_id = self.disposal_journal_id = False
        if self.category_id:
            self.disposal_account_id = self.category_id and self.category_id.disposal_account_id \
                and self.category_id.disposal_account_id.id or False
            self.disposal_journal_id = self.category_id and self.category_id.disposal_journal_id \
                and self.category_id.disposal_journal_id.id or False

    @api.constrains('disposal_date')
    def _check_disposal_date(self):
        if self.disposal_date:
            date_lst = []
            for line in self.depreciation_line_ids:
                if line.move_id:
                    date_lst.append(line.depreciation_date)
            if date_lst:
                last_move_date = max(date_lst)
                if self.disposal_date <= last_move_date:
                    raise ValidationError(_('Disposal Date must be greater than %s ' % (last_move_date)))
