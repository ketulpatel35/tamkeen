from odoo import models, api, fields, _


class HrHolidaysLog(models.Model):
    _name = 'hr.holidays.log'

    user_id = fields.Many2one('res.users', string='User')
    activity_datetime = fields.Datetime(string='Activity Datetime')
    state_from = fields.Char(string='State From')
    state_to = fields.Char(string='State To')
    reason = fields.Text(string='Reason')
    leave_id = fields.Many2one('hr.holidays', string='Leave')