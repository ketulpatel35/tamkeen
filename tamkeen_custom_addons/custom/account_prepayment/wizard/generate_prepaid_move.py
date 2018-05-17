# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, tools, api, fields


class GenerateMoves(models.TransientModel):
    _name = 'generate.prepaid.move'

    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    prepayment_type_ids = fields.Many2many('account.prepayment.type',
                                           'prepaid_move_prepayment_type_rel',
                                           'prepaid_move_id',
                                           'prepayment_type_id',
                                           'PrePayment Types'
                                           )

    @api.multi
    def generate_entries(self):
        prepayment_line_obj = self.env['account.prepayment.line']
        for rec in self:
            prepayment_type_ids = rec.prepayment_type_ids.ids
            if not prepayment_type_ids:
                prepayment_type_ids = self.env['account.prepayment.type'].search([]).ids
            domain = [('date', '<=', rec.date),
                      ('move_id', '=', False),
                      ('account_prepayment_id.state', '=', 'running'),
                      ('account_prepayment_id.prepayment_type_id', 'in', prepayment_type_ids)]
            for prepayment_rec in prepayment_line_obj.search(domain):
                prepayment_rec.create_move()
