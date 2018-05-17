from odoo import models, api, fields


class EmploymentContract(models.Model):
    _name = 'employment.contract'


    name = fields.Char(string='Reference')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee Company ID', store=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')