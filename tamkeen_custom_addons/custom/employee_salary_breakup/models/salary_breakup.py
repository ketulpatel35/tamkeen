# -*- coding: utf-8 -*-
##############################################################################
from odoo import fields, models


class HrContract(models.Model):
    _name = 'salary.breakup'

    name = fields.Char('Name')
    code = fields.Char('Code')
    amount = fields.Float('Amount')
    hr_contract_id = fields.Many2one('hr.contract', 'Employee Contract')
