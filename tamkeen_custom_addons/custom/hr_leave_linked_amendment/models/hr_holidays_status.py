from odoo import models, api, fields


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'


    linked_with_payroll = fields.Boolean(string='Linked With Payroll')
