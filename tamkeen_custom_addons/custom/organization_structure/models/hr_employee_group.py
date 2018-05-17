# -*- encoding: utf-8 -*-
from odoo import fields, api, models


class EmployeeGroup(models.Model):
    _name = 'hr.employee.group'
    _description = "Employee Group"

    _sql_constraints = [
        ('code_uniq', 'unique(short_name, company_id)',
         'Code should be unique per Employee Group!')]

    name = fields.Char(string='Employee Group Name')
    code = fields.Char(string='Code')
    short_name = fields.Char(string='Short Name')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    parent_id = fields.Many2one('hr.employee.group', string='Parent Group')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, index=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Company related to this journal")
