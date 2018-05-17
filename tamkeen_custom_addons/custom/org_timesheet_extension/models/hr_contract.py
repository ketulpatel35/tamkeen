from odoo import models, api, fields


class HrJobTemplate(models.Model):
    _inherit = 'hr.contract'

    timesheet_type = fields.Selection([('salaried', 'Salaried Employees'),
                                       ('hourly', 'Hourly Employees')],
                                      default='salaried', string='Timesheet '
                                                                 'Type')