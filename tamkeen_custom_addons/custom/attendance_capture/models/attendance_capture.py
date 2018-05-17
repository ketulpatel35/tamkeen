import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AttendanceCapture(models.Model):
    _name = 'attendance.capture.data'
    _description = 'Capture Attendance Data From Difference Machin' \
                   '(database) and stored hear'
    _rec_name = 'attendance_identifier'

    @api.depends('total')
    def _compute_total_hours(self):
        """
        compute total hours from total
        :return:
        """
        if self.total:
            try:
                unit_hours = datetime.datetime.strptime(
                    self.total, DEFAULT_SERVER_TIME_FORMAT)
                default_time = datetime.datetime.strptime(
                    '00:00:00', DEFAULT_SERVER_TIME_FORMAT)
                u_hour = unit_hours - default_time
                self.total_hours = float(u_hour.seconds) / 3600
            except:
                pass

    name = fields.Many2one('hr.employee', string='Employee')
    attendance_identifier = fields.Char('Attendance ID')
    first_in = fields.Datetime('First In')
    last_out = fields.Datetime('Last Out')
    in_out_per_day = fields.Char('In-Out per Day')
    diff_first_last = fields.Char('Diff.First In Last Out')
    error = fields.Text('Error')
    machine_identifier = fields.Char('Machin ID')
    location = fields.Char('Location')
    hr_attendance_id = fields.Many2one('hr.attendance', 'Hr Attendance')
    date = fields.Date('Date')
    att_type = fields.Char('Type')
    att_status = fields.Char('Status')
    total = fields.Char('Total')

    # total_hours = fields.Float('Total Hours',
    #                            compute='_compute_total_hours',
    #                            store=True)

    def get_total_hours(self, total):
        """
        get total hours in float
        :param total:
        :return:
        """
        total_hours = 0.00
        if total:
            try:
                unit_hours = datetime.datetime.strptime(
                    total, DEFAULT_SERVER_TIME_FORMAT)
                default_time = datetime.datetime.strptime(
                    '00:00:00', DEFAULT_SERVER_TIME_FORMAT)
                u_hour = unit_hours - default_time
                total_hours = float(u_hour.seconds) / 3600
                return total_hours
            except:
                return total_hours

    @api.model
    def check_total_diff(self, first_in, last_out):
        first_in_strp = datetime.datetime.strptime(
            first_in, DEFAULT_SERVER_DATETIME_FORMAT)
        last_out_strp = datetime.datetime.strptime(
            last_out, DEFAULT_SERVER_DATETIME_FORMAT)
        total = (last_out_strp - first_in_strp).days * 24 * 60 or False
        return total

    @api.model
    def get_first_in_last_out(self, att_capt_rec):
        first_in = False
        last_out = False

        if str(att_capt_rec.att_status) == 'LAST OUT before FIRST IN':
            first_in = att_capt_rec.last_out
            last_out = att_capt_rec.last_out
        elif str(att_capt_rec.att_status) == 'FIRST_IN equal LAST OUT':
            first_in = att_capt_rec.first_in
            last_out = att_capt_rec.last_out
        elif str(att_capt_rec.att_status) == 'CORRECT':
            first_in = att_capt_rec.first_in
            last_out = att_capt_rec.last_out
        elif str(att_capt_rec.att_status) == 'NOT HAVE FIRST_IN':
            # elif not att_capt_rec.first_in and att_capt_rec.last_out:
            first_in = att_capt_rec.last_out
            last_out = att_capt_rec.last_out
        elif str(att_capt_rec.att_status) == 'NOT HAVE LAST_OUT':
            # elif att_capt_rec.first_in and not att_capt_rec.last_out:
            first_in = att_capt_rec.first_in
            last_out = att_capt_rec.first_in
        elif att_capt_rec.first_in and att_capt_rec.last_out:
            total = self.check_total_diff(att_capt_rec.first_in,
                                          att_capt_rec.last_out)
            if total <= 2:
                att_capt_rec.write({'att_status': 'Total is less than 2 '
                                                  'minutes'})
                first_in = att_capt_rec.first_in
                last_out = att_capt_rec.last_out
        return first_in, last_out

    def _check_attendance(self, attendance_rec, current):
        real_attendance_rec = False
        for attendance in attendance_rec:
            attendance_date = \
                str(attendance.check_in).split(' ')[0]
            if str(current) == attendance_date:
                real_attendance_rec = attendance
                break
        return real_attendance_rec

    @api.model
    def create_attendance_record(self, first_in, last_out, emp_rec,
                                 att_capt_rec, total_hours):
        hr_attendance_obj = self.env['hr.attendance']
        attendance_rec = hr_attendance_obj.search(
            [('employee_id.attendance_identifier', '=',
              att_capt_rec.attendance_identifier)])
        real_attendance_rec = self._check_attendance(attendance_rec,
                                                     str(first_in).split(
                                                         ' ')[0])
        status = att_capt_rec.att_status
        if real_attendance_rec:
            status = 'Duplicate'

        hr_attendance_rec = hr_attendance_obj.create({
            'employee_id': emp_rec.id,
            'check_in': first_in,
            'machine_sign_in': first_in,
            'check_out': last_out,
            'machine_sign_out': last_out,
            'state': 'draft',
            'date': att_capt_rec.date,
            'total_hours': total_hours,
            'status': status,
        })
        return hr_attendance_rec

    @api.model
    def _update_attendance(self):
        """
        read employee attendance Update in hr attendance object.
        mapping based on attendance_identifier field whitch is unique for
        per employee.
        :return:
        """
        exist_employee_list = []
        employee_obj = self.env['hr.employee']
        for att_capt_rec in self.search([('hr_attendance_id', '=', False)]):
            if not att_capt_rec.attendance_identifier:
                att_capt_rec.error = 'Attendence ID was not mapped !'
                continue
            # find employee based on Attendence ID
            emp_rec = employee_obj.search([
                ('attendance_identifier', '=',
                 att_capt_rec.attendance_identifier)])
            exist_employee_list.append(emp_rec.id)
            if not emp_rec:
                att_capt_rec.error = 'Employee not mapped with this ' \
                                     'Attendence ID !'
                continue
            if len(emp_rec) > 1:
                att_capt_rec.error = 'Multipe Employee find with this ' \
                                     'Attendence ID !'
                continue
            # if att_capt_rec.first_in and att_capt_rec.last_out and \
            #         att_capt_rec.first_in > att_capt_rec.last_out:
            #     att_capt_rec.error = 'Check Out" time cannot be earlier' \
            #                          ' than "Check In" time.'
            #     continue
            if emp_rec:
                first_in, last_out = self.get_first_in_last_out(att_capt_rec)
                total_hours = self.get_total_hours(att_capt_rec.total)
                if first_in and last_out:
                    hr_attendance_rec = self.create_attendance_record(
                        first_in, last_out, emp_rec, att_capt_rec, total_hours)
                    att_capt_rec.write({
                        'hr_attendance_id': hr_attendance_rec.id,
                        'name': emp_rec.id,
                        'error': False,
                    })
                    # attendance_rec = hr_attendance_obj. \
                    #     search([('employee_id', '=', emp_rec.id),
                    #             ('date', '=', att_capt_rec.date)])
                    # if attendance_rec:
                    #     # if first_in < attendance_rec.check_in:
                    #     attendance_rec.write({'machine_sign_in': first_in,
                    #                           'machine_sign_out': last_out})
                    #     att_capt_rec.write({'hr_attendance_id':
                    # attendance_rec.id, 'error': False})
                    #     # if last_out > attendance_rec.check_out:
                    #     #     attendance_rec.write({})
                    #     # att_capt_rec.write({'hr_attendance_id':
                    #     # attendance_rec.id, 'error': False})
                    # first_in_d =\
                    #     datetime.datetime.strptime(first_in,
                    #                                DEFAULT_SERVER_DATETIME_FORMAT)
                    # last_out_d = \
                    #     datetime.datetime.strptime(last_out,
                    #                                DEFAULT_SERVER_DATETIME_FORMAT)
                    # if attendance_rec:
                    #     check_in_d = datetime.datetime.strptime(
                    #         attendance_rec.check_in,
                    #         DEFAULT_SERVER_DATETIME_FORMAT)
                    #     check_out_d = datetime.datetime.strptime(
                    #         attendance_rec.check_out,
                    #         DEFAULT_SERVER_DATETIME_FORMAT)
                    #     diff_hours = check_out_d - check_in_d
                    #     diff_h, diff_s, diff_m = 0, 0, 0
                    #     if diff_hours:
                    #         diff_h = int(str(diff_hours).split(':')[0])
                    #         diff_m = int(str(diff_hours).split(':')[1])
                    #         diff_s = int(str(diff_hours).split(':')[2])
                    #     if first_in <= attendance_rec.check_in and last_
                    # out >= \
                    #             attendance_rec.check_out:
                    #         attendance_rec.write({'check_in': first_in,
                    #                               'check_out': last_out})
                    #         att_capt_rec.write({
                    #             'hr_attendance_id': attendance_rec.id,
                    #             'error': False,
                    #         })
                    #     if attendance_rec.check_in >= last_out:
                    #         last_out_d_final = last_out_d - timedelta(
                    #             hours=diff_h, minutes=diff_m, seconds=diff_s)
                    #         attendance
                    # _rec.write({'check_out': last_out_d_final,
                    #                               })
                    #         att_capt_rec.write({
                    #             'hr_attendance_id': attendance_rec.id,
                    #             'error': False,
                    #         })
                    #     if attendance_rec.check_in < last_out:
                    #         attendance_rec.write({'check_out': last_out})
                    #         att_capt_rec.write({
                    #             'hr_attendance_id': attendance_rec.id,
                    #             'error': False,
                    #         })
                    #     if attendance_rec.check_in < first_in:
                    #         first_in_d_final = first_in_d -
                    #  timedelta(
                    #             hours=diff_h, minutes=diff_m, seconds=diff_s)
                    #         attendance_rec.write({'check_in': f
                    # irst_in_d_final})
                    #         att_capt_rec.write({
                    #             'hr_attendance_id': attendance_rec.id,
                    #             'error': False,
                    #         })
                    #     if attendance_rec.check_in > first_in:
                    #         attendance_rec.write({'check_in': first_in})
                    #         att_capt_rec.write({
                    #             'hr_attendance_id': attendance_rec.id,
                    #             'error': False,
                    #         })
                    # else:
                    #     hr_attendance_rec = hr_attendance_obj.create({
                    #         'employee_id': emp_rec.id,
                    #         'check_in': first_in,
                    #         'machine_sign_in': first_in,
                    #         'check_out': last_out,
                    #         'machine_sign_out': last_out,
                    #         'state': 'draft',
                    #         'date': att_capt_rec.date,
                    #         'total_hours': total_hours,
                    #         'status': att_capt_rec.att_status,
                    #     })
                    #     att_capt_rec.write({
                    #         'hr_attendance_id': hr_attendance_rec.id,
                    #         'name': emp_rec.id,
                    #         'error': False,
                    #     })

                    # if not date:
                    #     date = d.today() - timedelta(1)
                    #
                    # employee in leave
                    # for emp_rec_nxt in employee_obj.search([('id', 'not in',
                    #
                    #        exist_employee_list)]):
                    #     if emp_rec_nxt.attendance_identifier:
                    #         hr_attendance_rec = hr_attendance_obj.search(
                    #             [('employee_id', '=', emp_rec_nxt.id),
                    #              ('date', '=', date)])
                    #         if not hr_attendance_rec:
                    #             for holiday_req in s
                    # elf.env['hr.holidays'].search(
                    #                     [('employee_id', '=',
                    # emp_rec_nxt.id),('type', '=', 'remove'),
                    #                    ('state', 'in',
                    #  ['validate', 'leave_approved'])]):
                    #                 if not holiday_req.date_from or not \
                    #                         holiday_req.date_to:
                    #                     continue
                    #                 f_date = str(holiday_req.date_from).
                    # split(' ')[0]
                    #                 t_date = str(holiday_req.date_to).
                    # split(' ')[0]
                    #                 from_date = datetime.datetime.strptime(
                    #                     f_date,
                    #                     DEFAULT_SERVER_DATE_FORMAT).date()
                    #                 date = datetime.datetime.strptime(
                    #                     str(date),
                    # DEFAULT_SERVER_DATE_FORMAT).date()
                    #                 to_date = datetime.datetime.strptime(
                    #                     t_date,
                    #                     DEFAULT_SERVER_DATE_FORMAT).date()
                    #                 if from_date <= date <= to_date:
                    #                     date_in =
                    # datetime.datetime.strptime(
                    #                         str(date),
                    #  DEFAULT_SERVER_DATE_FORMAT)
                    #                     date_out = date_in +
                    # timedelta(hours=8)
                    #                     hr_attendance_rec =
                    #  hr_attendance_obj.create({
                    #                         'employee_id': emp_rec_nxt.id,
                    #                         'check_in': str(date_in),
                    #                         'machine_sign_in': str(date_in),
                    #                         'machine_sign_out':
                    #  str(date_out),
                    #                         'check_out': str(date_out),
                    #                         'state': 'draft',
                    #                         'date': str(date),
                    #                         'is_leave': True,
                    #                     })
                    #                     att_capt_rec.write({
                    #                         'hr_attendance_id':
                    #  hr_attendance_rec.id,
                    #                         'name': emp_rec.id,
                    #                         'error': False,
                    #                     })
                    #                     leave_employee_list.append(emp_rec_nxt.id)
                    #     emp_list = exist_employee_list + leave_employee_list
                    #
                    # employee absent(leave request not approved)
                    # for emp_rec_abs in employee_obj.search([
                    # ('id', 'not in', emp_list)]):
                    #     if emp_rec_abs.attendance_identifier:
                    #         hr_attendance_rec = hr_attendance_obj.search(
                    #             [('employee_id', '=', emp_rec_abs.id),
                    #              ('date', '=', date)])
                    #         if not hr_attendance_rec:
                    # date_in_out = datetime.datetime.strptime(
                    # str(date), DEFAULT_SERVER_DATE_FORMAT)
                    # current_date = d.strftime(d.today(), '%Y-%m-%d')
                    #             hr_attendance_obj.create({
                    #                 'employee_id': emp_rec_abs.id,
                    #                 'check_in': str(date) + ' 00:00:00',
                    #                 'check_out': str(date) + ' 00:00:00',
                    #                 'machine_sign_in': str(date) +
                    #  ' 00:00:00',
                    #                 'machine_sign_out': str(date) +
                    #  ' 00:00:00',
                    #                 'state': 'draft',
                    #                 'date': str(date),
                    #                 'is_absent': True,
                    #             })
                    #             emp_list.append(emp_rec_abs.id)
                    #             att_capt_rec.write({
                    #                 'hr_attendance_id': hr_attendance_rec.id,
                    #                 'name': emp_rec.id,
                    #                 'error': False,
                    #             })
