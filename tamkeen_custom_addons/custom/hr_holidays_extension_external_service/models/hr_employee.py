from odoo import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    outside_employee = fields.Boolean(string='Outside Resource')
    external_service_manager = fields.Many2one('res.users', string='External '
                                                                   'Manager')
