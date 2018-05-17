# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    prepeyment_line_ids = fields.One2many('account.prepayment.line', 'move_id', string='Prepayment Lines', ondelete="restrict")

    @api.multi
    def button_cancel(self):
        for move in self:
            for line in move.prepeyment_line_ids:
                line.move_posted_check = False
        return super(AccountMove, self).button_cancel()

    @api.multi
    def post(self):
        for move in self:
            for depreciation_line in move.prepeyment_line_ids:
                depreciation_line.post_lines_and_close_asset()
        return super(AccountMove, self).post()
