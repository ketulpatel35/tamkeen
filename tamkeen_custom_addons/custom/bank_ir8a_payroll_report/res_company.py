# -*- coding: utf-8 -*-
from odoo import fields, models


class res_company(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    mol_establishment_id = fields.Char(string='MOL Establishment ID',
                                       default='12-123456789123456',
                                       help='A unique ID provided by Minister '
                                            'of Labour needs to be caputred '
                                            'here,it’s a numeric field it '
                                            'should be in the format of 2!d - '
                                            '15!d (99-999999999999999)')
    connect_id = fields.Char(string='Connect ID', default='ABC74849001',
                             help='Connect ID with the bank.')
    # payroll_bank = fields.Many2one('res.bank', string='Payroll Bank')
    payroll_partner_bank =\
        fields.Many2one('res.partner.bank',
                        string='Payroll Account Number', required=1)
