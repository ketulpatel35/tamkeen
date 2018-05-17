# -*- coding: utf-8 -*-

from odoo import fields, models


class res_company(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    hr_group_email = fields.Char(string='HR Group Email',
                                 default='hr@company.com')
    fi_group_email = fields.Char(string='Finance Group Email',
                                 default='fi@company.com')
    prcrmnt_group_email = fields.Char(string='Procurement Group Email',
                                      default='procurement@company.com')
