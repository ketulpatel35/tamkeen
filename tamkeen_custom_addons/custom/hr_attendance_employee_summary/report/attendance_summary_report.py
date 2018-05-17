from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone


class HrAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.hr_attendance_employee_summary.report_attendancessummary'

    def _get_header_info(self, start_date, end_date):
        st_date = fields.Date.from_string(start_date)
        en_date = fields.Date.from_string(end_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(en_date)
        }

    def _get_rest_days(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    def _get_day(self, start_date, end_date):
        res = []
        context = self._context
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        month_days = (end_date - start_date).days + 1
        if context:
            employee_active_id = self._context.get('active_id')
            employee_rec = self.env['hr.employee'].browse(employee_active_id)
            rest_days = self._get_rest_days(employee_rec)
            # rest_days = employee_rec.contract_id.working_hours.get_rest_days()
        for x in range(0, month_days):
            color = '#ababab' if start_date.weekday() in rest_days else ''
            # color = '#ababab' if start_date.strftime('%a') == 'Sat' or
            # start_date.strftime('%a') == 'Sun' else ''
            res.append({'day_str': start_date.strftime('%a'),
                        'day': start_date.day, 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_months(self, start_date, end_date):
        # it works for geting month name between two dates.
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'),
                        'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res

    # def check_attendance(self, attendance_rec, current):
    #     real_attendance_rec = False
    #     for attendance in attendance_rec:
    #         attendance_date = \
    #             str(attendance.check_in).split(' ')[0]
    #         if str(current) == attendance_date:
    #             real_attendance_rec = attendance
    #             break
    #     return real_attendance_rec

    def riyadh_timezone(self, date):
        gmt_tz = timezone('GMT')
        if self.env.user and self.env.user.tz:
            local_tz = timezone(self.env.user.tz)
        else:
            local_tz = timezone('Asia/Riyadh')
        if date:
            gmt_utcdt = (gmt_tz.localize(date))
            riyadh_dt = gmt_utcdt.astimezone(local_tz)
            return riyadh_dt
        return date

    def convert_in_time(self, hours):
        seconds = hours * 60 * 60
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return hours, minutes

    def get_public_holidays(self, year, employee):
        public_holidays_obj = self.env['hr.holidays.public']
        p_holidays_date = []
        p_holidays_line = public_holidays_obj.get_holidays_list(year, employee)
        for line in p_holidays_line:
            p_holidays_date.append(line.date)
        return p_holidays_date

    def get_check_in_out(self, attendance):
        if attendance.check_in:
            check_in = attendance.check_in
        elif not attendance.check_in and attendance.check_out:
            check_in = attendance.check_out
        else:
            check_in = datetime.today()
        if attendance.check_out:
            check_out = attendance.check_out
        elif attendance.check_in and not attendance.check_out:
            check_out = attendance.check_in
        else:
            check_out = datetime.today()
        return check_in, check_out

    def _get_attendance_summary(self, start_date, end_date, employee_rec):
        res = []
        todays_date = datetime.now().date()
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        month_days = (end_date - start_date).days + 1
        rest_days = self._get_rest_days(employee_rec)
        # rest_days = employee_rec.contract_id.working_hours.get_rest_days()
        total_worked_hours, total_permission_hours = 0.00, 0.00
        for index in range(0, month_days):

            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': '', 'worked_hours': '',
                        'check_in': '', 'check_out': '', 'permission_hours':
                            '', 'check_in_color': '', 'check_out_color': ''})
            attendance = self.env['hr.attendance']. \
                search([('employee_id', '=', employee_rec.id),
                        ('check_in', '<=', str(current)),
                        ('check_out', '>=', str(current)),
                        ('status', '!=', str('Duplicate'))], limit=1)
            # attendance = self.check_attendance(attendance_rec, current)
            holidays_rec = self.env['hr.holidays'] \
                .search([('employee_id', '=', employee_rec.id),
                         ('state', 'in', ('leave_approved',
                                          'validate')),
                         ('date_from', '<=', str(current)),
                         ('date_to', '>=', str(current)), ('type', '!=',
                                                           'add'
                                                           )],
                        limit=1)

            public_holidays_list = self.get_public_holidays(
                start_date.year, employee_rec.id)

            if current.weekday() in rest_days and not attendance:
                res[index]['check_in_color'] = '#ababab'
                res[index]['check_out_color'] = '#ababab'

            elif str(current) in public_holidays_list and not attendance:
                attendance_config_rec = \
                    self.env['attendance.report.config'].search([
                        ('public_holidays', '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name

            elif holidays_rec:
                attendance_config_rec = self.env[
                    'attendance.report.config'].search([('leave',
                                                         '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name

            elif current and employee_rec and attendance and attendance.status:
                check_in, check_out = self.get_check_in_out(attendance)
                # Check In Riyadh Timezone
                check_in_strp = datetime.strptime(
                    check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                check_in_riyadh = self.riyadh_timezone(check_in_strp)

                # Check Out Riyadh Timezone
                check_out_strp = datetime.strptime(
                    check_out, DEFAULT_SERVER_DATETIME_FORMAT)
                check_out_riyadh = self.riyadh_timezone(check_out_strp)

                if attendance.status == 'CORRECT' \
                        or attendance.status == 'Attendance Updated(Sign in)' \
                        or attendance.status == 'Attendance Updated(Sign out)':
                    res[index]['check_in'] = str(
                        datetime.strftime(check_in_riyadh, '%H:%M'))
                    res[index]['check_out'] = str(
                        datetime.strftime(check_out_riyadh, '%H:%M'))

                elif (attendance.status).strip() == 'NOT HAVE FIRST_IN':
                    attendance_config_rec = \
                        self.env['attendance.report.config'].search([
                            ('forget_check_in', '=', True)], limit=1)
                    res[index]['check_in_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_out'] = str(
                        datetime.strftime(check_out_riyadh, '%H:%M'))
                elif (attendance.status).strip() in \
                        ['LAST OUT before FIRST IN',
                         'FIRST_IN equal LAST OUT',
                         'Total is less than 2 minutes']:
                    attendance_config_rec = \
                        self.env['attendance.report.config'].search([
                            ('last_out_before_first_in', '=', True)], limit=1)
                    res[index]['check_in_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_out_color'] = \
                        attendance_config_rec.color_name

                elif (attendance.status).strip() == 'NOT HAVE LAST_OUT':
                    attendance_config_rec = \
                        self.env['attendance.report.config'].search([
                            ('forget_check_out', '=', True)], limit=1)
                    res[index]['check_out_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_in'] = str(
                        datetime.strftime(check_in_riyadh, '%H:%M'))

                if attendance.status and attendance.status \
                        not in ['LAST OUT before FIRST IN',
                                'FIRST_IN equal LAST OUT',
                                'Total is less than 2 minutes']:
                    w_hours, w_minutes = self.convert_in_time(
                        attendance.worked_hours)
                    worked_hours = "%02d:%02d" % (w_hours, w_minutes)
                    res[index]['worked_hours'] = worked_hours
                if attendance.status not in \
                        ['LAST OUT before FIRST IN',
                         'FIRST_IN equal LAST OUT',
                         'Total is less than 2 minutes']:
                    total_worked_hours += attendance.worked_hours

                if attendance.permission_hours and attendance.status:
                    p_hours, p_minutes = self.convert_in_time(
                        attendance.permission_hours)
                    permission_worked_hours = "%02d:%02d" % (p_hours,
                                                             p_minutes)
                    res[index]['permission_hours'] = \
                        permission_worked_hours
                    total_permission_hours += attendance.permission_hours
            elif current < todays_date:
                attendance_config_rec = self.env[
                    'attendance.report.config'].search([('absent',
                                                         '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name
        t_hours, t_minutes = self.convert_in_time(total_worked_hours)
        total_worked_hours_time = "%02d:%02d" % (t_hours, t_minutes)

        t_p_hours, t_p_minutes = self.convert_in_time(total_permission_hours)
        total_p_worked_hours_time = "%02d:%02d" % (t_p_hours, t_p_minutes)

        return {'res': res, 'total_worked_hours': total_worked_hours_time,
                'total_permission_hours': total_p_worked_hours_time}

    def _get_employee_name(self):
        context = dict(self._context)
        if context and context.get('active_id'):
            employee_active_id = context.get('active_id')
            employee_active_rec = \
                self.env['hr.employee'].browse(employee_active_id)
            return employee_active_rec

    def _get_data_from_report(self, data):
        res = [{'data': []}]
        employee_active_rec = self._get_employee_name()
        if employee_active_rec:
            attendance_summary = self._get_attendance_summary(
                data['date_from'], data['date_to'], employee_active_rec)
            res[0]['data'].append({
                'emp': employee_active_rec.name,
                'display': attendance_summary.get('res'),
                'total_wh': attendance_summary.get('total_worked_hours'),
                'total_ph': attendance_summary.get('total_permission_hours'),
            })
        return res

    def _get_attendance_config(self):
        res = []
        for attendance in self.env['attendance.report.config'].search([]):
            res.append({
                'color': attendance.color_name,
                'name': attendance.name
            })
        return res

    @api.model
    def render_html(self, docids, data=None):
        Report = self.env['report']
        docargs = {
            'employee_name': self._get_employee_name().name,
            'get_header_info': self._get_header_info(
                data['form']['date_from'], data['form']['date_to']),
            'get_day': self._get_day(data['form']['date_from'],
                                     data['form']['date_to']),
            'get_months': self._get_months(data['form']['date_from'],
                                           data['form']['date_to']),
            'get_data_from_report': self._get_data_from_report(data['form']),
            'get_attendance_config': self._get_attendance_config(),
        }
        return Report.render(
            'hr_attendance_employee_summary.report_attendancessummary',
            docargs)
