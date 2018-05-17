from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    application_id = fields.Many2one('hr.applicant', 'Application')

    _sql_constraints = [
        ('unique_identification_id', 'unique(identification_id)',
         ('Identifications Number must be unique!'))]
