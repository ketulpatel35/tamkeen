try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields
import base64
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from cStringIO import StringIO
from days360 import get_date_diff_days360


class LeaveCleansingXLSReport(models.TransientModel):
    _name = 'leave.cleansing.xls.report'

    employee_ids = fields.Many2many('hr.employee',
                                    'cleansing_report_employee_rel',
                                    'rep_id', 'emp_id',
                                    string='Select Employees')
    holiday_status_id = fields.Many2one('hr.holidays.status',
                                        string='Leave Type')
    to_date = fields.Date('Till Date', default=datetime.today().date())

    @api.model
    def set_header(self, worksheet, workbook, till_date):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        worksheet.row(0).height = 250
        headers_name = ['Employee Name',
                        'Employee Company ID',
                        'Leave Type', 'Department', 'Cost Center',
                        'Allocated Balance (Outside)',
                        'Allocated Balance (ERP)',
                        'Total Requested Leaves',
                        'Total Remaining Balance (Outside)',
                        'Total Remaining Balance (ERP)']

        header_col = 0
        xlwt.add_palette_colour("c_light_gray", 0x22)
        workbook.set_colour_RGB(0x22, 237, 236, 234)
        xlwt.add_palette_colour("c_dark_gray", 0x23)
        workbook.set_colour_RGB(0x23, 177, 176, 174)
        xlwt.add_palette_colour("c_dark_red", 0x24)
        workbook.set_colour_RGB(0x24, 182, 31, 16)
        top_header = 'Leaves Report :' + str(till_date)
        s0_header = xlwt.easyxf(
            'font: bold 1,height 200 ,colour yellow;'
            'pattern: pattern solid, fore_colour c_dark_gray;'
            'borders: left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(0, 0, 0, 8, top_header, s0_header)
        s0 = xlwt.easyxf(
            'font: bold 1,height 180 ,colour c_dark_red;'
            'alignment: horizontal center, wrap 1;'
            'pattern: pattern solid, fore_colour c_light_gray;'
            'borders: left thin, right thin, top thin, bottom thin;')
        # flag use for change background color
        for h_name in headers_name:
            worksheet.col(header_col).width = 256 * 20
            worksheet.write_merge(1, 2, header_col, header_col, h_name, s0)
            header_col += 1

    @api.model
    def get_allocated_balance_today_outside(self, emp_rec, till_date):
        if not emp_rec.initial_employment_date:
            return False
        s_date = datetime.strptime(emp_rec.initial_employment_date,
                                   DEFAULT_SERVER_DATE_FORMAT).date()
        all_days = get_date_diff_days360(s_date, till_date)
        return all_days * 0.083333

    @api.multi
    def _get_allocate_leave(self, emp_rec, holiday_status_rec):
        holidays_rec = self.env['hr.holidays'].search([
            ('employee_id', '=', emp_rec.id),
            ('holiday_status_id', '=', holiday_status_rec.id),
            ('state', '=', 'validate'),
            ('type', '=', 'add')])
        allocate_leave = 0
        for holidays in holidays_rec:
            if holidays.number_of_days_temp:
                allocate_leave += holidays.number_of_days_temp
        return allocate_leave

    @api.model
    def _get_allocated_balance_today_erp(self, emp_rec, holiday_status_rec):
        """
        :param emp_rec:
        :param holiday_status_rec:
        :return:
        """
        # for now take All Allocation Leave till today Date
        allocate_leave = self._get_allocate_leave(
            emp_rec, holiday_status_rec)
        holiday_obj = self.env['hr.holidays']
        future_balance = holiday_obj.with_context(
            {'holiday_status_rec': holiday_status_rec}
        )._calculate_emp_future_accrued_days(emp_rec, False)
        return allocate_leave + future_balance

    @api.model
    def _get_total_leave_request(self, emp_rec, holiday_status_rec, till_date):
        """
        :param emp_rec:
        :param holiday_status_rec:
        :return:
        """
        state_list = ('draft', 'refuse', 'cancel')
        requested_leave_balance = 0.0
        holidays_rec = self.env['hr.holidays'].search([
            ('state', 'not in', state_list), ('employee_id', '=', emp_rec.id),
            ('holiday_status_id', '=', holiday_status_rec.id),
            ('type', '=', 'remove')])
        for holiday in holidays_rec:
            to_date = datetime.strptime(holiday.date_to.split(' ')[0],
                                        DEFAULT_SERVER_DATE_FORMAT).date()
            if to_date <= till_date:
                if holiday.number_of_days_temp:
                    requested_leave_balance += holiday.number_of_days_temp
            else:
                from_date = datetime.strptime(
                    holiday.date_from.split(' ')[0],
                    DEFAULT_SERVER_DATE_FORMAT).date()
                if from_date <= till_date <= to_date:
                    if holiday.number_of_days_temp:
                        data_vals = holiday.count_number_of_days_temp(
                            from_date, till_date)
                        if data_vals:
                            requested_leave_balance += data_vals.get(
                                'real_days')
        return requested_leave_balance

    @api.model
    def _get_remaining_balance(self, alb_out, alb_erp, total_leave_request):
        """
        :param alb_out:
        :param alb_erp:
        :param total_leave_request:
        :return:
        """
        rem_bal_out = int(alb_out) - int(total_leave_request)
        rem_bal_erp = int(alb_erp) - int(total_leave_request)
        bal_status = False
        if rem_bal_out == rem_bal_erp:
            bal_status = True

        return {'bal_status': bal_status, 'out': rem_bal_out,
                'erp': rem_bal_erp}

    @api.model
    def get_lines_data(self, worksheet, till_date):
        """
        :return:
        """
        if len(self.employee_ids) > 0:
            employee_rec = self.employee_ids
        else:
            employee_rec = self.env['hr.employee'].search([])
        if self.holiday_status_id:
            holiday_status_rec = self.holiday_status_id
        else:
            holiday_status_rec = self.env['hr.holidays.status'].search([
                ('code', '=', 'ANNLV')])
        s3 = xlwt.easyxf(
            'font: height 180 ,colour black;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;')
        row_num = 3
        if holiday_status_rec:
            for emp_rec in employee_rec:
                # exl Write data
                worksheet.write(row_num, 0, emp_rec.name, s3)
                worksheet.write(row_num, 1, emp_rec.f_employee_no, s3)
                worksheet.write(row_num, 2, holiday_status_rec.name, s3)
                worksheet.write(row_num, 3, emp_rec.department_id.name)
                worksheet.write(row_num, 4, emp_rec.job_id and
                                emp_rec.job_id.analytic_account_id or
                                '')
                alb_out = self.get_allocated_balance_today_outside(
                    emp_rec, till_date)
                worksheet.write(row_num, 5, int(alb_out), s3)
                alb_erp = self._get_allocated_balance_today_erp(
                    emp_rec, holiday_status_rec)
                worksheet.write(row_num, 6, int(alb_erp), s3)
                total_leave_request = self._get_total_leave_request(
                    emp_rec, holiday_status_rec, till_date)
                worksheet.write(row_num, 7, int(total_leave_request), s3)
                rem_bal_vals = self._get_remaining_balance(alb_out, alb_erp,
                                                           total_leave_request)
                s4 = xlwt.easyxf(
                    'font: height 180 ,colour blue;'
                    'alignment: horizontal center, wrap 1;'
                    'pattern: pattern solid, fore_colour white;'
                    'borders: left thin, right thin, top thin, bottom thin;')
                s5 = xlwt.easyxf(
                    'font: height 180 ,colour red;'
                    'alignment: horizontal center, wrap 1;'
                    'pattern: pattern solid, fore_colour white;'
                    'borders: left thin, right thin, top thin, bottom thin;')
                if rem_bal_vals.get('bal_status'):
                    worksheet.write(row_num, 8, int(rem_bal_vals.get(
                        'out')), s4)
                    worksheet.write(row_num, 9, int(rem_bal_vals.get(
                        'erp')), s4)
                else:
                    worksheet.write(row_num, 8, int(rem_bal_vals.get(
                        'out')), s5)
                    worksheet.write(row_num, 9, int(rem_bal_vals.get(
                        'erp')), s5)
                row_num += 1

    @api.multi
    def print_report(self):
        """
        Leave Cleansing xls Report
        :return: {}
        """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Leave Balance xls Report')
        # add new colour to palette and set RGB colour value
        # header and Data getting
        to_date = self.to_date
        if not to_date:
            to_date = str(datetime.today().date())
        till_date = datetime.strptime(to_date,
                                      DEFAULT_SERVER_DATE_FORMAT).date()
        self.set_header(worksheet, workbook, till_date)
        self.get_lines_data(worksheet, till_date)
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(3)
        stream = StringIO()
        workbook.save(stream)
        print_link = self.env['cleansing.xls.report'].create(
            {'name': 'Leave Balance Report.xls',
             'xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cleansing.xls.report',
            'res_id': print_link.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
