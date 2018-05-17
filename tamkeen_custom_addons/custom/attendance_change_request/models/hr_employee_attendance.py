from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import Warning
from pytz import timezone
from dateutil.relativedelta import relativedelta


class HrAttMaster(models.Model):
    _inherit = 'hr.attendance'

    # @api.multi
    @api.one
    @api.depends('attendance_change_request_ids')
    def _compute_permission_hours(self):
        total_hours = 0.0
        for rec in self:
            for change_request in rec.attendance_change_request_ids:
                if change_request.permission:
                    delta = datetime.strptime(
                        change_request.date_to, DEFAULT_SERVER_DATETIME_FORMAT
                    ) - datetime.strptime(change_request.date_from,
                                          DEFAULT_SERVER_DATETIME_FORMAT)
                    total_hours += delta.total_seconds() / 3600.0
            rec.permission_hours = total_hours

    def get_configuration_time(self, attendance_config_rec):
        if attendance_config_rec:
            work_from = attendance_config_rec.work_from
            buffer_time = attendance_config_rec.buffer_hours
            work_to = attendance_config_rec.work_to
        return work_from, buffer_time, work_to

    def check_attendance_configuration(self, work_from_split,
                                       buffer_time_split, work_to_split):
        if len(work_from_split) != 3 or len(buffer_time_split) != 3 \
                or len(work_to_split) != 3:
            raise Warning(_('Please check Attendance'
                            ' configuration or contact to your HR '
                            'Team'))

    def riyadh_timezone(self, date):
        date = fields.Datetime.from_string(date)
        gmt_tz = timezone('GMT')
        if self.env.user and self.env.user.tz:
            local_tz = timezone(self.env.user.tz)
        else:
            local_tz = timezone('Asia/Riyadh')
        if date:
            gmt_utcdt = (gmt_tz.localize(date))
            riyadh_dt = gmt_utcdt.astimezone(local_tz)
            return fields.Datetime.to_string(riyadh_dt)
        return date

    @api.multi
    # @api.depends('check_in', 'check_out')
    def _get_late_in(self):
        configuration_obj = self.env['attendance.configuration']
        for rec in self:
            attendance_config_rec = configuration_obj.search([], limit=1)
            if attendance_config_rec:
                work_from, buffer_time, work_to = \
                    rec.get_configuration_time(attendance_config_rec)
                work_from_split = work_from.split(':')
                buffer_time_split = buffer_time.split(':')
                work_to_split = work_to.split(':')
                # Check Configuration
                rec.check_attendance_configuration(
                    work_from_split, buffer_time_split, work_to_split)
                rec.late_in_out = False
                if rec.check_in:
                    check_in_strp = \
                        datetime.strptime(rec.check_in,
                                          DEFAULT_SERVER_DATETIME_FORMAT)
                    check_in_with_timezone = self.riyadh_timezone(rec.check_in)

                    check_in = check_in_strp + relativedelta(hour=int(
                        work_from_split[0]), minute=int(work_from_split[1]),
                        second=int(work_from_split[2]))
                    check_in_with_buffer = check_in + relativedelta(
                        hours=int(buffer_time_split[0]), minutes=int((
                            buffer_time_split[1])), seconds=int(
                            buffer_time_split[2]))
                    check_in_with_buffer_str = datetime.strftime(
                        check_in_with_buffer, DEFAULT_SERVER_DATETIME_FORMAT)
                    if check_in_with_timezone > check_in_with_buffer_str:
                        rec.late_in_out = True
                if rec.check_out and rec.late_in_out is not True:
                    check_out_riyadh_timezone = self.riyadh_timezone(
                        rec.check_out)

                    check_out_split = rec.check_out.split(' ')[0]

                    check_out = check_out_split + ' %s:%s:%s' % (
                        str(work_to_split[0]), str(work_to_split[1]),
                        str(work_to_split[2]))
                    if check_out_riyadh_timezone < check_out:
                        rec.late_in_out = True

    manual_attendance = fields.Boolean('is manual attendance')
    permission_hours = fields.Float(string='Permission Hours',
                                    compute='_compute_permission_hours',
                                    store=True)
    attendance_change_request_ids = fields.One2many(
        'attendance.change.request', 'attendance_id',
        string='Attendance Change Request')
    machine_sign_in = fields.Datetime(string='Machine Sign In')
    machine_sign_out = fields.Datetime(string='Machine Sign Out')
    late_in_out = fields.Boolean(string='Late In / Early Out',
                                 compute='_get_late_in')
    late_in_out_compute = fields.Boolean(related='late_in_out',
                                         string='Late In / Early Out',
                                         store=True)
