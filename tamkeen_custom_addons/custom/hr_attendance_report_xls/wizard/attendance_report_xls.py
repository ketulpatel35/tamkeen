try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields
import datetime as dt
import base64
from datetime import datetime, timedelta
from cStringIO import StringIO
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone


class hr_attendance_report_xls(models.TransientModel):
    _inherit = 'hr.attendance.report.xls'

    def _get_day(self, start_date, end_date):
        '''
        This method is used for fetch the day by start date and end date.
        :param start_date: Report Start Date
        :param end_date: Report End Date
        :return:List of Dictionary
        '''
        res = []
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        month_days = (end_date - start_date).days + 1
        for x in range(0, month_days):
            res.append(
                {'date': str(start_date),
                 })
            start_date = start_date + relativedelta(days=1)
        return res

    # def real_attendance_rec(self, attendance_rec, current):
    #     '''
    #     This method is used for search attendance record.
    #     :param attendance_rec:Attendance Record
    #     :param current: Date
    #     :return: Search Attendance Record and return.
    #     '''
    #     real_attendance_rec = False
    #     for attendance in attendance_rec:
    #         attendance_date = \
    #             str(attendance.check_in).split(' ')[0]
    #         if str(current) == attendance_date:
    #             real_attendance_rec = attendance
    #             break
    #     return real_attendance_rec

    def riyadh_timezone(self, date):
        '''
        :param date: Date
        :return: Date with Riyadh Timezone
        '''
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

    def get_attendance_hour_minute(self, attendance):
        if attendance.check_in:
            check_in = attendance.check_in
        elif not attendance.check_in and attendance.check_out:
            check_in = attendance.check_out
        else:
            check_in = datetime.today()
        check_in_strp = datetime.strptime(check_in,
                                          DEFAULT_SERVER_DATETIME_FORMAT)
        check_in_riyadh = self.riyadh_timezone(check_in_strp)
        if attendance.check_out:
            check_out = attendance.check_out
        elif attendance.check_in and not attendance.check_out:
            check_out = attendance.check_in
        else:
            check_out = datetime.today()
        check_out_strp = datetime.strptime(check_out,
                                           DEFAULT_SERVER_DATETIME_FORMAT)
        check_out_riyadh = self.riyadh_timezone(check_out_strp)
        check_in_h = '%02d' % check_in_riyadh.hour
        check_out_h = '%02d' % check_out_riyadh.hour
        check_in_m = '%02d' % check_in_riyadh.minute
        check_out_m = '%02d' % check_out_riyadh.minute

        return check_in_h, check_out_h, check_in_m, check_out_m

    def convert_in_time(self, hours):
        # seconds = hours * 60 * 60
        # minutes, seconds = divmod(seconds, 60)
        minutes = hours * 60
        hours, minutes = divmod(minutes, 60)
        return hours, round(minutes, 2)

    def get_public_holidays(self, year, employee):
        public_holidays_obj = self.env['hr.holidays.public']
        p_holidays_date = []
        p_holidays_line = public_holidays_obj.get_holidays_list(year, employee)
        for line in p_holidays_line:
            p_holidays_date.append(line.date)
        return p_holidays_date

    def get_summary(self, employee, date_from, date_to):
        res = []
        if employee and date_from and date_to:
            start_date = fields.Date.from_string(date_from)
            end_date = fields.Date.from_string(date_to)
            todays_date = datetime.now().date()
            month_days = (end_date - start_date).days + 1
            rest_days = employee.contract_id. \
                working_hours.get_rest_days()
            for index in range(0, month_days):
                current = start_date + timedelta(index)
                res.append({'day': current.day, 'color': '',
                            'worked_hours': '', 'check_in': '',
                            'check_out': '', 'permission_hours': '',
                            'is_holiday': '', 'is_absent': '',
                            'public_holiday': False})

                attendance = self.env['hr.attendance']. \
                    search([('employee_id', '=', employee.id),
                            ('check_in', '<=', str(current)),
                            ('check_out', '>=', str(current)),
                            ('status', '!=', str('Duplicate'))], limit=1)
                # attendance = self.real_attendance_rec(
                #     attendance_rec, current)
                holidays_rec = self.env['hr.holidays'] \
                    .search([('employee_id', '=', employee.id),
                             ('state', 'in', ('leave_approved',
                                              'validate')),
                             ('date_from', '<=', str(current)),
                             ('date_to', '>=', str(current)), ('type', '!=',
                                                               'add'
                                                               )],
                            limit=1)
                public_holidays_list = self.get_public_holidays(
                    start_date.year, employee.id)
                self.get_public_holidays(start_date.year, employee.id)
                if current.weekday() in rest_days and not attendance:
                    res[index]['color'] = '#ababab'
                elif str(current) in public_holidays_list and not attendance:
                    res[index]['public_holiday'] = True
                elif holidays_rec:
                    holiday_name = 'L'
                    if holidays_rec.holiday_status_id and \
                            holidays_rec.holiday_status_id.code:
                        holiday_name = 'L / ' + \
                                       holidays_rec.holiday_status_id.code
                    res[index][
                        'is_holiday'] = holiday_name
                elif attendance and attendance.status:
                    check_in_h, check_out_h, check_in_m, check_out_m = \
                        self.get_attendance_hour_minute(attendance)
                    if attendance.status == \
                            'CORRECT' or attendance.status == \
                            'Attendance Updated(Sign in)' \
                            or attendance.status == 'Attendance Updated(Sign' \
                                                    ' out)':
                        res[index]['check_in'] = (check_in_h + ':' +
                                                  check_in_m)
                        res[index]['check_out'] = (check_out_h + ':' +
                                                   check_out_m)
                    elif (attendance.status).strip() == 'NOT HAVE FIRST_IN':
                        res[index]['check_out'] = (check_out_h + ':' +
                                                   check_out_m)
                    elif (attendance.status).strip() == 'NOT HAVE LAST_OUT':
                        res[index]['check_in'] = (check_in_h + ':' +
                                                  check_in_m)
                    elif (attendance.status).strip() \
                            in ['LAST OUT before FIRST IN',
                                'FIRST_IN equal LAST OUT',
                                'Total is less than 2 minutes']:
                        res[index]['check_in'] = 'WF'
                        res[index]['check_out'] = 'WF'
                    if attendance.status:
                        worked_hours = attendance.worked_hours
                        if attendance.worked_hours < 0:
                            worked_hours = 0.0
                        res[index]['worked_hours'] = str(worked_hours)
                        if attendance.worked_hours > 8.0:
                            additional_hours = attendance.worked_hours - 8.0
                            res[index]['additional_hours'] = str(
                                additional_hours)
                    if attendance.permission_hours and attendance.status:
                        res[index]['permission_hours'] = str(
                            attendance.permission_hours)
                elif current < todays_date:
                    res[index][
                        'is_absent'] = 'A'
        return res

    def department_wise_employee(self, department_rec, date_from, date_to):
        department_lst = []
        if department_rec:
            for department in department_rec:
                dept_employees = self.env['hr.employee'].search([(
                    'department_id', '=', department.id)])
                for employee in dept_employees:
                    employee_summary = self.get_summary(
                        employee, date_from, date_to)
                    department_lst.append({'employee_id': employee,
                                           'department_id': department,
                                           'summary': employee_summary})
        else:
            departments = self.env['hr.department'].search([])
            for department in departments:
                dept_employees = self.env['hr.employee'].search(
                    [('department_id',
                      '=', department.id)])
                for employee in dept_employees:
                    employee_summary = self.get_summary(
                        employee, date_from, date_to)
                    department_lst.append({'employee_id': employee,
                                           'department_id': department,
                                           'summary': employee_summary})
        return department_lst

    @api.model
    def set_header(self, worksheet):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """

        worksheet.row(0).height = 600
        worksheet.row(1).height = 350
        worksheet.row(2).height = 320
        worksheet.row(3).height = 320
        t_col = 102
        for for_col in range(0, t_col):
            worksheet.col(for_col).width = 256 * 20
        # s0 = xlwt.easyxf(
        #     'font: bold 1,height 180 ,colour h1_text_color;'
        #     'alignment: horizontal center;'
        #     'pattern: pattern_back_colour gray40 ,fore_colour gray40;'
        #     'borders: left thin, right thin, top thin, bottom thin;')

        s1 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')

        s2 = xlwt.easyxf(
            'font: bold 1,height 260 ,colour h2_text_color;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40'
        )

        ss3 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour h2_text_color;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40'
        )

        ss3_green = xlwt.easyxf(
            'font: bold 1,height 180 ,colour green;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40'
        )

        header_0 = "Attendance Report from %s to %s" % (str(self.date_from),
                                                        str(self.date_to))
        worksheet.write_merge(0, 0, 0, 2, header_0, s1)
        worksheet.write_merge(1, 1, 0, 0, 'Employee Name', ss3)
        worksheet.write_merge(1, 1, 1, 1, 'Employee Company ID', ss3)
        worksheet.write_merge(1, 1, 2, 2, 'Department', ss3)
        # header_3 = "Attendance Report from %s to %s" % (str(self.date_from),
        #                                                 str(self.date_to))
        # worksheet.write_merge(0, 0, 4, 9, header_3, s1)
        get_days = self._get_day(self.date_from, self.date_to)
        s3 = xlwt.easyxf(
            'font: bold 1,height 280;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour white,'
            'fore_colour white')

        """
            1. Sign in
            2. Sign out
            3. Working Hours
            4. Additional Hours
            5. Permission Hours
        """
        label_lst = []
        if self.sign_in:
            label_lst.append('Sign In')
        if self.sign_out:
            label_lst.append('Sign out')
        if self.working_hours:
            label_lst.append('Working Hours')
        if self.additional_hours:
            label_lst.append('Additional Hours')
        if self.permission_hours:
            label_lst.append('Permission Hours')
        ss1 = xlwt.easyxf(
            'font: bold 1, height 180, colour h1_text_color;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        start = 3
        for flag in range(len(get_days)):
            start_flag = False
            for label in label_lst:
                if not start_flag:
                    end = start + len(label_lst) - 1
                    days_name = "%s" % get_days[flag].get('date')
                    worksheet.write_merge(0, 0, start, end, days_name, s2)
                    start_flag = True
                if label != 'Permission Hours':
                    worksheet.write_merge(1, 1, start, start, label, ss1)
                else:
                    worksheet.write_merge(1, 1, start, start, label, ss3_green)
                start += 1
                flag += 1
        # Total Working Hours
        total_hours_header = "Total Working Hours"
        worksheet.write_merge(1, 1, start, start + 1, total_hours_header, s3)
        start += 2

        # Total Permission Hours
        permission_total_hours_header = "Total Permission Hours"
        worksheet.write_merge(1, 1, start, start + 1,
                              permission_total_hours_header, s3)
        start += 1

    def get_lines_data(self, worksheet):
        '''
        This method is used for attendance data filter by Departments
        :param worksheet: Used for add line in xls report
        :return: Data
        '''
        employee_department = self.department_wise_employee(
            self.department_ids, self.date_from, self.date_to)
        column_start = 2

        s6 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour black;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;')
        s7 = xlwt.easyxf(
            'font: bold 1,height 280;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour orange,'
            'fore_colour orange')
        s8 = xlwt.easyxf(
            'font: bold 1,height 280;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore_colour custom_colour')
        for department in employee_department:
            total_worked_hours, total_permission_hours = 0.0, 0.0
            row_start = 0

            employee_company_id = department.get('employee_id').f_employee_no \
                if department.get('employee_id') and department.get(
                'employee_id').f_employee_no else ''

            employee_name = department.get('employee_id').name if \
                department.get('employee_id') and department.get(
                    'employee_id').name else ''

            department_name = department.get('department_id').name if \
                department.get('department_id') and department.get(
                    'department_id').name else ''

            worksheet.write(column_start, row_start, employee_name, s6)
            row_start += 1
            worksheet.write(column_start, row_start, employee_company_id, s6)
            row_start += 1
            worksheet.write(column_start, row_start, department_name, s6)
            sign_in_start = row_start + 1
            for values in department.get('summary'):
                if values.get('color'):
                    if self.sign_in:
                        worksheet.write(column_start, sign_in_start, '', s7)
                        sign_in_start += 1
                    if self.sign_out:
                        worksheet.write(column_start, sign_in_start, '', s7)
                        sign_in_start += 1
                    if self.working_hours:
                        worksheet.write(column_start, sign_in_start, '', s7)
                        sign_in_start += 1
                    if self.additional_hours:
                        worksheet.write(column_start, sign_in_start, '', s7)
                        sign_in_start += 1
                    if self.permission_hours:
                        worksheet.write(column_start, sign_in_start, '', s7)
                        sign_in_start += 1
                elif values.get('public_holiday'):
                    # for holidays in range(5):
                    if self.sign_in:
                        worksheet.write(column_start, sign_in_start, '', s8)
                        sign_in_start += 1
                    if self.sign_out:
                        worksheet.write(column_start, sign_in_start, '', s8)
                        sign_in_start += 1
                    if self.working_hours:
                        worksheet.write(column_start, sign_in_start, '', s8)
                        sign_in_start += 1
                    if self.additional_hours:
                        worksheet.write(column_start, sign_in_start, '', s8)
                        sign_in_start += 1
                    if self.permission_hours:
                        worksheet.write(column_start, sign_in_start, '', s8)
                        sign_in_start += 1
                elif values.get('is_holiday'):
                    # for holiday_line in range(3):
                    if self.sign_in:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_holiday'), s6)
                        sign_in_start += 1
                    if self.sign_out:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_holiday'), s6)
                        sign_in_start += 1
                    if self.working_hours:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_holiday'), s6)
                        sign_in_start += 1
                    if self.additional_hours:
                        worksheet.write(column_start, sign_in_start, '', s6)
                        sign_in_start += 1
                    if self.permission_hours:
                        worksheet.write(column_start, sign_in_start, '', s6)
                        sign_in_start += 1
                elif values.get('is_absent'):
                    # for absent_line in range(3):
                    if self.sign_in:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_absent'), s6)
                        sign_in_start += 1
                    if self.sign_out:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_absent'), s6)
                        sign_in_start += 1
                    if self.working_hours:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('is_absent'), s6)
                        sign_in_start += 1
                    if self.additional_hours:
                        worksheet.write(column_start, sign_in_start, '', s6)
                        sign_in_start += 1
                    if self.permission_hours:
                        worksheet.write(column_start, sign_in_start, '', s6)
                        sign_in_start += 1
                else:
                    # 1. Sign in
                    if self.sign_in:
                        print "\n\nself.sign_in", self.sign_in
                        worksheet.write(column_start, sign_in_start,
                                        values.get('check_in'), s6)
                        sign_in_start += 1

                    # 2. Sign out
                    if self.sign_out:
                        worksheet.write(column_start, sign_in_start,
                                        values.get('check_out'), s6)
                        sign_in_start += 1

                    # 3. Working Hours
                    worked_hours = values.get('worked_hours')
                    if worked_hours:
                        w_hours, w_minutes = self.convert_in_time(
                            float(worked_hours))
                        worked_hours = "%02d:%02d" % (w_hours, w_minutes)
                    if self.working_hours:
                        worksheet.write(column_start, sign_in_start,
                                        worked_hours, s6)
                        sign_in_start += 1

                    # 4. Additional Hours
                    additional_worked_hours = values.get('additional_hours')
                    if additional_worked_hours:
                        a_hours, a_minutes = self.convert_in_time(
                            float(additional_worked_hours))
                        additional_worked_hours = "%02d:%02d" % (a_hours,
                                                                 a_minutes)
                    if self.additional_hours:
                        worksheet.write(column_start, sign_in_start,
                                        additional_worked_hours, s6)

                        sign_in_start += 1

                    # 5. Permission Hours
                    permission_worked_hours = values.get('permission_hours')
                    if permission_worked_hours:
                        p_hours, p_minutes = self.convert_in_time(
                            float(permission_worked_hours))
                        permission_worked_hours = "%02d:%02d" % (p_hours,
                                                                 p_minutes)
                    if self.permission_hours:
                        worksheet.write(column_start, sign_in_start,
                                        permission_worked_hours, s6)
                        sign_in_start += 1

                    # Total Worked Hours
                    if values.get('worked_hours'):
                        total_worked_hours += float(values.get('worked_hours'))
                    # Total Permission Hours
                    if values.get('permission_hours'):
                        total_permission_hours += float(values.get(
                            'permission_hours'))
            t_hours, t_minutes = self.convert_in_time(total_worked_hours)
            total_worked_hours_time = "%02d:%02d" % (t_hours, t_minutes)
            worksheet.write_merge(column_start, column_start, sign_in_start,
                                  sign_in_start + 1,
                                  total_worked_hours_time, s6)
            sign_in_start += 2
            t_p_hours, t_p_minutes = self.convert_in_time(
                total_permission_hours)
            total_p_worked_hours_time = "%02d:%02d" % (t_p_hours, t_p_minutes)
            worksheet.write_merge(column_start, column_start, sign_in_start,
                                  sign_in_start + 1,
                                  total_p_worked_hours_time, s6)
            column_start += 1
            sign_in_start += 1

    @api.model
    def _get_attachment(self, data):
        """
        create and return attachment
        :param data:
        :return:
        """
        today_date = dt.date.today()
        attachment_data = {
            'name': 'Attendance_Report_' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas_fname': 'Attendance_Report_' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas': base64.encodestring(data),
            'res_model': '',
            'res_id': False,
            'mimetype': 'application/vnd.ms-excel'
        }
        attachment_rec = self.env['ir.attachment'].create(attachment_data)
        return attachment_rec

    @api.multi
    def print_report(self):
        """
        Attendance Report
        :return: {}
        """

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Attendance Report')
        # add new colour to palette and set RGB colour value
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 160, 122)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        self.get_lines_data(worksheet)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(2)
        worksheet.set_vert_split_pos(3)

        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['att.report.print.link'].create(
            {'name': 'Attendance Report.xls',
             'xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'att.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
