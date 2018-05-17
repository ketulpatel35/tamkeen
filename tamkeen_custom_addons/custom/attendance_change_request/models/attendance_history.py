from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    hr_attendance_history_ids = fields.One2many('hr.attendance.history',
                                                'attendance_id',
                                                string='Attendance History')

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        if vals.get('check_in') or vals.get('check_out'):
            new_check_in = old_check_in = self.check_in
            new_check_out = old_check_out = self.check_out
            if vals.get('check_in'):
                new_check_in = vals.get('check_in')
            if vals.get('check_out'):
                new_check_out = vals.get('check_out')

            vals = {'references': self._context.get('change_request').ref,
                    'old_checkin_date': old_check_in,
                    'old_checkout_date': old_check_out,
                    'new_checkin_date': new_check_in,
                    'new_checkout_date': new_check_out,
                    'updated_by': self.env.user.id,
                    'attendance_id': self.id}
            self.env['hr.attendance.history'].create(vals)
        return super(HrAttendance, self).write(vals)


class HrAttanenceHistory(models.Model):
    _name = 'hr.attendance.history'

    references = fields.Char(string='References')
    attendance_id = fields.Many2one('hr.attendance', string='Attendance')
    old_checkin_date = fields.Datetime(string="Old Check In",
                                       track_visibility='always')
    old_checkout_date = fields.Datetime(string='Old Checkout',
                                        track_visibility='always')
    new_checkin_date = fields.Datetime(string="New Check In",
                                       track_visibility='always')
    new_checkout_date = fields.Datetime(string='New Checkout',
                                        track_visibility='always')
    updated_by = fields.Many2one('res.users', string='Updated By')
    updated_time = fields.Datetime('Updated Date', default=fields.Datetime.now)
