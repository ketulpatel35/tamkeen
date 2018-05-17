from odoo import models, api, fields


class TimeRecordingLog(models.Model):
    _name = 'time.recording.log'

    user_id = fields.Many2one('res.users', string='User')
    activity_datetime = fields.Datetime(string='Activity Datetime')
    state_from = fields.Char(string='State From')
    state_to = fields.Char(string='State To')
    time_record_id = fields.Many2one('sheet.time.recording.line',
                                     string='Time Recording')