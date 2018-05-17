# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    arabic_name = fields.Char(string='Arabic Name', copy=False)
    display_in_ess_payslip = fields.Boolean(string='Display in Self Service('
                                                   'Payslip)', copy=False)