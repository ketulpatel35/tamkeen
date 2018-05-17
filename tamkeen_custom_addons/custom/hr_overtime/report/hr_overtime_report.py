try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
import time
from cStringIO import StringIO
import base64
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class HrOvertimeReportXls(models.TransientModel):
    _name = 'hr.overtime.report.xls'

    @api.multi
    def _check_group(self):
        return True if self.env.user.has_group(
            'hr_overtime.group_display_overtime_cost') else False

    date_from = fields.Date(string='Date From',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To')
    sort_by = fields.Selection([('employee', 'Employee'),
                                ('department', 'Department')], string='Sort '
                                                                      'By')
    is_cost_center = fields.Boolean(string='Cost Center', default=True)
    is_pre_requested_hours = fields.Boolean(string='Pre-Requested Hours',
                                            default=True)
    is_actual_taken_hours = fields.Boolean(string='Actual Taken Hours',
                                           default=True)
    is_attendance_hours = fields.Boolean(string='Attendance Hours',
                                         default=True)
    is_day_type = fields.Boolean(string='Day Type', default=True)
    is_status = fields.Boolean(string='Status', default=True)
    is_employee_hourly_rate = fields.Boolean(string='Empoloyee Hourly Rate',
                                             default=_check_group)
    employee_ids = fields.Many2many('hr.employee',
                                    'overtime_report_employee_rel',
                                    'report_id', 'emp_id', string='Employees')
    cost_center_ids = fields.Many2many('account.analytic.account',
                                       'overtime_report_cost_center_rel',
                                       'report_id', 'cost_center_id',
                                       string='Cost Center')
    overtime_claim_policy_id = fields.Many2one('service.configuration.panel',
                                               string='Policy')
    stage_id = fields.Many2many('service.panel.displayed.states',
                                string='Status', index=True,
                                domain="[('service_type_ids', '=', "
                                       "overtime_claim_policy_id)]")

    @api.model
    def default_get(self, fields):
        res = super(HrOvertimeReportXls, self).default_get(fields)
        if self.env.user.company_id:
            if not self.env.user.company_id.overtime_policy_id:
                raise Warning(_('Need to configure Overtime Policy in '
                                'Company!'))
            res.update({'overtime_claim_policy_id': self.env.user.company_id
                       .overtime_policy_id.id})
        return res

    @api.onchange('date_from', 'date_to')
    def onchange_date_from(self):
        date_from_strp = datetime.strptime(self.date_from,
                                           DEFAULT_SERVER_DATE_FORMAT)
        add_days_from_strp = date_from_strp + relativedelta(days=30)
        add_days_from_strf = datetime.strftime(add_days_from_strp,
                                               DEFAULT_SERVER_DATE_FORMAT)
        next_month_date = date_from_strp + relativedelta(months=1, day=1)
        last_date = next_month_date - relativedelta(days=1)
        last_date_strf = datetime.strftime(last_date,
                                           DEFAULT_SERVER_DATE_FORMAT)
        if self.date_from and not self.date_to:
            self.date_to = last_date_strf

        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise \
                    Warning(
                        _('Date from must be earlier than Date to.'))
            if self.date_to > add_days_from_strf:
                self.date_to = add_days_from_strf

    def _get_day(self, date_from, date_to):
        '''
        This method is used for fetch the day by start date and end date.
        :param start_date: Report Start Date
        :param end_date: Report End Date
        :return:List of Dictionary
        '''
        res = []
        start_date = fields.Date.from_string(date_from)
        end_date = fields.Date.from_string(date_to)
        month_days = (end_date - start_date).days + 1
        for x in range(0, month_days):
            res.append(
                {'date': str(start_date),
                 })
            start_date = start_date + relativedelta(days=1)
        return res

    @api.model
    def get_claim_rec(self):
        """
        get employee which use in overtime claim
        :return:
        """
        domain = []
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.cost_center_ids:
            domain.append(('cost_center_id', 'in', self.cost_center_ids.ids))
        if self.stage_id:
            domain.append(('stage_id', 'in', self.stage_id.ids))
        return self.env['overtime.statement.request'].search(domain)

    @api.model
    def set_header(self, worksheet):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        worksheet.row(0).height = 600
        worksheet.row(1).height = 750
        for for_col in range(0, 3):
            worksheet.col(for_col).width = 256 * 20
        for for_col in range(0, 100):
            worksheet.col(for_col).width = 256 * 19
        s1 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        s2 = xlwt.easyxf(
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
        header_0 = "Overtime Report from %s to %s" % (str(self.date_from),
                                                      str(self.date_to))
        worksheet.write_merge(0, 0, 0, 3, header_0, s1)
        worksheet.write_merge(1, 1, 0, 0, 'Employee Name', s2)
        worksheet.write_merge(1, 1, 1, 1, 'Employee Company ID', s2)
        worksheet.write_merge(1, 1, 2, 2, 'Department', s2)
        worksheet.write_merge(1, 1, 3, 3, 'Position', s2)
        """
            1. Cost Center
            2. Pre-Requested Hours
            3. Actual Taken Hours
            4. Attendance Hours
            5. Day Type
            6. Status
            7. Empoloyee Hourly Rate
        """
        ss1 = xlwt.easyxf(
            'font: bold 1, height 180, colour h1_text_color;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')

        label_lst = []
        if self.is_cost_center:
            label_lst.append('Cost Center')
        if self.is_pre_requested_hours:
            label_lst.append('Pre-Requested Hours')
        if self.is_actual_taken_hours:
            label_lst.append('Actual Taken Hours')
        if self.is_attendance_hours:
            label_lst.append('Attendance Hours')
        if self.is_day_type:
            label_lst.append('Day Type')
        if self.is_status:
            label_lst.append('Status')
        if self.is_employee_hourly_rate:
            label_lst.append('Empoloyee Hourly Rate')
        get_days = self._get_day(self.date_from, self.date_to)
        s3 = xlwt.easyxf(
            'font: bold 1,height 180,colour blue;;'
            'alignment: horizontal center;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour white,'
            'fore_colour white')

        start = 4
        for flag in range(len(get_days)):
            start_flag = False
            for label in label_lst:
                if not start_flag:
                    end = start + len(label_lst) - 1
                    days_name = "%s" % get_days[flag].get('date')
                    worksheet.write_merge(0, 0, start, end, days_name, s2)
                    start_flag = True
                if label != 'Empoloyee Hourly Rate':
                    worksheet.write_merge(1, 1, start, start, label, ss1)
                else:
                    worksheet.write_merge(1, 1, start, start, label, ss3_green)
                start += 1
                flag += 1
        # Total Working Hours
        total_hours_header = "Total Pre-Requested Hours"
        worksheet.write_merge(1, 1, start, start + 1, total_hours_header,
                              s3)
        start += 2

        # Total Permission Hours
        permission_total_hours_header = "Total Taken Hours"
        worksheet.write_merge(1, 1, start, start + 1,
                              permission_total_hours_header, s3)
        start += 1

    @api.model
    def get_attendance_hour(self, employee_rec, date):
        """
        :param employee_rec:
        :param date:
        :return:
        """
        att_hr = 0.00
        att_rec = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_rec.id),
            ('date', '=', date)])
        if att_rec:
            att_hr = int(att_rec.worked_hours)
        return att_hr

    @api.model
    def get_employee_hourly_rate(self, employee_rec):
        """
        get employee hourly rate from contract
        :return:
        """
        hourly_rate = 0.00
        if employee_rec.contract_id:
            hourly_rate = employee_rec.contract_id.hourly_rate
        return hourly_rate

    @api.model
    def get_overtime_claim_line_data(self, claim_rec):
        """
        get overtime claim line wise data
        :param claim_rec: claim statement record
        :return:
        """
        res = []
        cc = claim_rec.cost_center_id.name if claim_rec.cost_center_id else ''
        stage_name = claim_rec.stage_id.name if claim_rec.stage_id else ''
        f_date = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        e_date = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        common_data = {
            'emp_name': claim_rec.employee_id.name,
            'emp_company': claim_rec.employee_id.f_employee_no,
            'emp_department': claim_rec.employee_id.department_id.name,
            'emp_position': claim_rec.employee_id.job_id.name,
            'cost_center': cc,
            'status': stage_name}
        cal_obj = self.env['overtime.calculation.line']
        for line_rec in claim_rec.overtime_claim_activity_ids:
            c_date = datetime.strptime(
                line_rec.date, DEFAULT_SERVER_DATE_FORMAT)
            if f_date <= c_date <= e_date:
                d_type = cal_obj._check_date_day_type(line_rec.date,
                                                      claim_rec.employee_id)
                if d_type:
                    if d_type == 'public_holiday':
                        day_type = 'Public Holiday'
                    elif d_type == 'rest_day':
                        day_type = 'Week End'
                    else:
                        day_type = 'Working Day'
                line_data = common_data.copy()
                # Get Attendance Hour
                attendance_hr = self.get_attendance_hour(claim_rec.employee_id,
                                                         line_rec.date)
                # Get Employee Hourly Rate
                hourly_rate = self.get_employee_hourly_rate(claim_rec.employee_id)
                line_data.update({'date': line_rec.date,
                                  'pre_req_hr': line_rec.expected_hours,
                                  'actual_taken_hr': line_rec.actual_hours,
                                  'attendance_hr': attendance_hr,
                                  'day_type': day_type,
                                  'hourly_rate': hourly_rate})
                res.append(line_data)
        return res

    def get_lines_data(self):
        '''
        This method is used for attendance data filter by Departments
        :param worksheet: Used for add line in xls report
        :return: Data
        '''
        report_data = []
        if self.date_to and self.date_from:
            claim_recs = self.get_claim_rec()
            """
            - set header and data in one method
            - check code for record as well
            """
            for c_rec in claim_recs:
                claim_line_data = self.get_overtime_claim_line_data(c_rec)
                report_data += claim_line_data
            if self.sort_by:
                if self.sort_by == 'cost_center':
                    report_data = sorted(report_data,
                                         key=lambda x: x['cost_center'])
                if self.sort_by == 'employee':
                    report_data = sorted(report_data,
                                         key=lambda x: x['emp_name'])
                if self.sort_by == 'department':
                    report_data = sorted(report_data,
                                         key=lambda x: x['emp_department'])
        return report_data

    @api.model
    def set_line_data(self, worksheet, line_data):
        """
        set line in excel report
        :param worksheet: excel object
        :param line_data: line data
        :return:
        """
        total_pre_requested_hours = 0.0
        total_taken_hours = 0.0
        row = 2
        for line_dict in line_data:
            start_date = fields.Date.from_string(self.date_from)
            end_date = fields.Date.from_string(self.date_to)
            month_days = (end_date - start_date).days + 1
            col = 0
            worksheet.write(row, col, line_dict.get('emp_name'))
            col += 1
            worksheet.write(row, col, line_dict.get('emp_company'))
            col += 1
            worksheet.write(row, col, line_dict.get('emp_department'))
            col += 1
            worksheet.write(row, col, line_dict.get('emp_position'))
            col += 1
            for date_range in range(0, month_days):
                current_date = start_date + timedelta(date_range)
                cost_center = pre_req_hr = actual_taken_hr = attendance_hr = \
                    day_type = status = hourly_rate = ''
                if line_dict.get('date') == str(current_date):
                    cost_center = line_dict.get('cost_center')
                    pre_req_hr = line_dict.get('pre_req_hr')
                    actual_taken_hr = line_dict.get('actual_taken_hr')
                    attendance_hr = line_dict.get('attendance_hr')
                    day_type = line_dict.get('day_type')
                    status = line_dict.get('status')
                    hourly_rate = line_dict.get('hourly_rate')
                    total_pre_requested_hours = line_dict.get('pre_req_hr')
                    total_taken_hours = line_dict.get('actual_taken_hr')
                if self.is_cost_center:
                    worksheet.write(row, col, cost_center)
                    col += 1
                if self.is_pre_requested_hours:
                    worksheet.write(row, col, pre_req_hr)
                    col += 1
                if self.is_actual_taken_hours:
                    worksheet.write(row, col, actual_taken_hr)
                    col += 1
                if self.is_attendance_hours:
                    worksheet.write(row, col, attendance_hr)
                    col += 1
                if self.is_day_type:
                    worksheet.write(row, col, day_type)
                    col += 1
                if self.is_status:
                    worksheet.write(row, col, status)
                    col += 1
                if self.is_employee_hourly_rate:
                    worksheet.write(row, col, hourly_rate)
                    col += 1
            if total_pre_requested_hours:
                worksheet.write(row, col, total_pre_requested_hours)
                col += 1
            else:
                worksheet.write(row, col, 0)
                col += 1
            if total_taken_hours:
                worksheet.write(row, col, total_taken_hours)
            else:
                worksheet.write(row, col, 0)
            row += 1

    @api.multi
    def print_overtime_report(self):
        """
       Attendance xls Report
       :return: {}
       """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Overtime Report')
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 160, 122)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        line_data = self.get_lines_data()
        self.set_line_data(worksheet, line_data)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(2)
        worksheet.set_vert_split_pos(4)

        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['overtime.report.print.link'].create(
            {'name': 'Overtime Report.xls',
             'overtime_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'overtime.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class AttReportPringLink(models.Model):
    _name = 'overtime.report.print.link'

    overtime_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Overtime_Report.xls')
