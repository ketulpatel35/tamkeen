from feedparser import _EndBracketRegEx

try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, fields, _
import time
from cStringIO import StringIO
import datetime as DT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DFTIME
import base64
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class PayrollReportXls(models.TransientModel):
    _name = 'payroll.period.report.xls'

    date_from = fields.Datetime(string='Date From', readonly=True)
    date_to = fields.Datetime(string='Date To', readonly=True)
    payrol_period_id = fields.Many2one('hr.payroll.period', string='Payroll')
    nationality = fields.Boolean('Nationality', default=True)
    working_days = fields.Boolean('Working Days', default=True)
    net = fields.Boolean('Net', default=True)
    salary_information = fields.Boolean('Salary Information As in Contract',
                                        default=True)
    cost_center = fields.Boolean('Cost Center', default=True)
    hiring_date = fields.Boolean('Hiring Date', default=True)
    notes = fields.Boolean('Notes', default=True)
    overtime = fields.Boolean('Overtime', default=True)
    exclude_overtime = fields.Boolean('Overtime', default=True)
    exclude_loan = fields.Boolean('Loan')
    employee_ids = fields.Many2many('hr.employee',
                                    'payroll_report_employee_rel',
                                    'payroll_id', 'emp_id', string='Employees')
    # in sort by cost_center Remaining
    sort_by = fields.Selection([('employee', 'Employee'),
                                ('department', 'Department'),
                                ('net', 'Net')], string='Sort By')

    @api.model
    def default_get(self, fields):
        """
        set default payroll period id.
        :param fields:
        :return:
        """
        res = super(PayrollReportXls, self).default_get(fields)
        if not self._context.get('active_id'):
            today_date = datetime.today()
            first_date_of_month = today_date.replace(day=1)
            lastMonth_date = first_date_of_month - timedelta(days=1)
            payroll_period_obj = self.env['hr.payroll.period']
            payroll_period_rec = payroll_period_obj.search([
                ('state', 'in', ('open', 'ended')),
                ('date_start', '>=', str(lastMonth_date))],
                order="date_start", limit=1)
            res['payrol_period_id'] = payroll_period_rec.id
        elif self._context.get('active_id'):
            res['payrol_period_id'] = self._context.get('active_id')
        return res

    @api.onchange('payrol_period_id')
    def onchange_payrol_period_id(self):
        res = {}
        if self.payrol_period_id and self.payrol_period_id.date_start and \
           self.payrol_period_id.date_end:
            self.date_from = self.payrol_period_id.date_start
            self.date_to = self.payrol_period_id.date_end
        res.update({'payrol_period_id': [('state', 'in', ['open', 'ended','generate'])]})
        return {'domain': res}

    @api.multi
    def get_month_year(self, end_date):
        # if hr_payroll_period_rec and hr_payroll_period_rec.register_id:
        #     if hr_payroll_period_rec.register_id.run_ids:
        #         date_end = hr_payroll_period_rec.register_id.run_ids[
        #             0].date_end
        month = datetime.strptime(end_date, DFTIME).strftime('%B')
        year = datetime.strptime(end_date, DFTIME).strftime('%Y')
        return month, year

    @api.model
    def get_display_column(self):
        """
        :param param:
        :return: return list of column to be display in report.
        """
        emp_clm = 3
        slr_clm = 0
        ear_clm = 7
        col_dis = ['Employee ID', 'Employee Name']
        if self.nationality:
            col_dis.append('Nationality')
            emp_clm += 1
        col_dis += ['Job Name', 'Department']
        if self.cost_center:
            col_dis.append('Cost Center')
            emp_clm += 1
        if self.working_days:
            col_dis.append('Working Days')
            emp_clm += 1
        if self.hiring_date:
            col_dis.append('Hire Date')
            emp_clm += 1
        if self.salary_information:
            col_dis += ['Basic', 'Housing', 'Transport', 'Rare Allowance']
            slr_clm += 3
        if self.overtime:
            col_dis += ['Basic', 'Housing', 'Transport', 'Rare Allowance',
                        'Overtime', 'Cost of Living Allowance', 'Other '
                                                                'Earnings',
                        'Total Earnings']
            ear_clm += 1
        else:
            col_dis += ['Basic', 'Housing', 'Transport', 'Rare Allowance',
                        'Cost of Living Allowance',
                        'Other Earnings', 'Total Earnings']
        col_dis += ['GOSI', 'Loan Deduction', 'Other Deductions', 'Total '
                                                'Deductions']
        return emp_clm, slr_clm, ear_clm, col_dis

    @api.model
    def set_header(self, worksheet, end_date):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        # hr_payroll_period_rec = self.env['hr.payroll.period'].browse(period_id)
        worksheet.row(0).height = 400
        worksheet.row(3).height = 320
        t_col = 28
        for for_col in range(0, t_col):
            if for_col in [4, 19, 20]:
                worksheet.col(for_col).width = 256 * 12
            elif for_col == 23:
                worksheet.col(for_col).width = 256 * 30
            else:
                worksheet.col(for_col).width = 256 * 10

        s1 = xlwt.easyxf(
            'font: bold 1,height 280;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour yellow,'
            'fore_colour yellow')
        month, year = self.get_month_year(end_date)
        if month and year:
            header_1 = "Employee Payslips for the Period: %s - %s" % (month,
                                                                      year)
        else:
            header_1 = "Employee Payslips"
        worksheet.write_merge(0, 0, 0, 7, header_1, s1)
        s2 = xlwt.easyxf(
            'font: bold 1,height 180;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid,'
            'pattern_back_colour yellow, fore_colour yellow')
        header_2 = 'Total Earnings (=Basic + Housing + Transportation + Rare' \
                   ' + Other Earnings)'
        worksheet.write_merge(1, 1, 0, 7, header_2, s2)
        header_3 = 'Total Deductions (=GOSI + Other Deductions)'
        worksheet.write_merge(2, 2, 0, 7, header_3, s2)
        emp_clm, slr_clm, ear_clm, col_dis = self.get_display_column()
        header_4 = 'Employee Information'
        s3 = xlwt.easyxf(
            'font: bold 1,height 200;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour yellow,'
            'fore_colour yellow;'
            'alignment: horizontal center;')
        col_start = 0
        col_end = emp_clm
        worksheet.write_merge(3, 3, col_start, col_end, header_4, s3)
        s4 = xlwt.easyxf(
            'font: bold 1,height 200;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour green,'
            'fore_colour green;'
            'alignment: horizontal center;')
        # Freeze column
        worksheet.set_vert_split_pos(emp_clm+1)
        if slr_clm != 0:
            header_5 = 'Salary Information as in Contract'
            col_start = col_end + 1
            col_end = col_start + slr_clm
            worksheet.write_merge(3, 3, col_start, col_end,
                                  header_5, s4)

        header_6 = 'Period Earnings (Accrued Period Salary)'
        s5 = xlwt.easyxf(
            'font: bold 1,height 200;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour blue,'
            'fore_colour blue;'
            'alignment: horizontal center;')
        col_start = col_end + 1
        col_end = col_start + (ear_clm - 1)
        worksheet.write_merge(3, 3, col_start, col_end, header_6, s5)
        header_7 = 'Deductions'
        s6 = xlwt.easyxf(
            'font: bold 1,height 200;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour red,'
            'fore_colour red;'
            'alignment: horizontal center;')
        col_start = col_end + 1
        col_end = col_start + 3
        worksheet.write_merge(3, 3, col_start, col_end, header_7, s6)
        if self.net:
            col_start = col_end + 1
            col_end = col_start
            worksheet.write_merge(3, 4, col_start, col_end, 'Net', s4)
        s6 = xlwt.easyxf(
            'font: bold 1,height 190;'
            'alignment: horizontal center,wrap 1;')
        if self.notes:
            col_start = col_end + 1
            col_end = col_start
            worksheet.write_merge(3, 4, col_start, col_end, 'Note', s6)
        h_8_col = 0
        worksheet.row(4).height = 850
        for h_8 in col_dis:
            worksheet.write(4, h_8_col, label=h_8, style=s6)
            h_8_col += 1
        return worksheet

    def _get_payslips(self, start_date, end_date):
        payslip_obj = self.env['hr.payslip']
        start_date = datetime.strptime(start_date, DFTIME).date()
        end_date = datetime.strptime(end_date, DFTIME).date()
        payslip_rec = payslip_obj.search([('date_from', '>=', start_date),
                                    ('date_to', '<=', end_date)])
        return payslip_rec

    @api.multi
    def _get_slip_details(self, start_date, end_date):
        """
        get details
        :param period_id:
        :return:
        """
        # hr_payroll_period_rec = self.env['hr.payroll.period'].browse(period_id)
        payslip_rec = self._get_payslips(start_date, end_date)
        res = []
        data = {}
        # if hr_payroll_period_rec and hr_payroll_period_rec.register_id:
        #     for run in hr_payroll_period_rec.register_id.run_ids:
        for slip in payslip_rec:
            if not self.employee_ids.ids or \
                            slip.contract_id.employee_id.id in \
                            self.employee_ids.ids:
                hire_date = slip.contract_id.employee_id.initial_employment_date
                unpaid_days = 0.0
                if slip.worked_days_line_ids:
                    for line in slip.worked_days_line_ids:
                        if line.code == 'UNP':
                            unpaid_days += line.number_of_days
                work_days = \
                    slip.number_of_days_new_employee - unpaid_days or 0
                data = {
                    'name': slip.contract_id.employee_id.name,
                    'dep': slip.contract_id.department_id.name,
                    'work_days': work_days,
                    'wage': slip.contract_id.wage,
                    'emp_id': slip.contract_id.employee_id.f_employee_no,
                    'country':
                        slip.contract_id.employee_id.country_id.name,
                    'job': slip.contract_id.job_id.name,
                    'hire_date': hire_date,
                }
                cost_center_id = ''
                if slip.contract_id.employee_id.job_id and \
                        slip.contract_id.employee_id.job_id.analytic_account_id:
                    cost_center_id += slip.contract_id.employee_id.job_id.analytic_account_id.code
                data.update({'cost_center_id': cost_center_id})
                data.update({
                    'BASIC': 0, 'BDED': 0, 'BNET': 0, 'HA': 0, 'HADED': 0,
                    'HANET': 0, 'TA': 0, 'TADED': 0, 'TANET': 0, 'CA': 0,
                    'CADED': 0, 'CANET': 0, 'RA': 0, 'RADED': 0,
                    'RANET': 0, 'FXDALW': 0, 'FXDALWDED': 0,
                    'FXDALWNET': 0, 'ADED': 0, 'ALW': 0, 'GOSI': 0,
                    'TDED': 0, 'ADED': 0, 'OT': 0, 'OE': 0, 'LNDED': 0,
                    'OD': 0,
                    'TTLERNG': 0, 'CLANET': 0,
                    'TTLDED': 0, 'GROSS': 0, 'NET': 0, 'note': '',
                })
                total_allowance = total_deduction = 0
                for line in slip.line_ids:
                    if line.code == 'BASIC':
                        data.update({'BASIC': line.total})
                    if line.code == 'BDED':
                        data.update({'BDED': line.total})
                    if line.code == 'BNET':
                        data.update({'BNET': line.total})

                    if line.code == 'HA':
                        data.update({'HA': line.total})
                    if line.code == 'HADED':
                        data.update({'HADED': line.total})
                    if line.code == 'HANET':
                        data.update({'HANET': line.total})

                    if line.code == 'TA':
                        data.update({'TA': line.total})
                    if line.code == 'TADED':
                        data.update({'TADED': line.total})
                    if line.code == 'TANET':
                        data.update({'TANET': line.total})

                    if line.code == 'CA':
                        data.update({'CA': line.total})
                    if line.code == 'CADED':
                        data.update({'CADED': line.total})
                    if line.code == 'CANET':
                        data.update({'CANET': line.total})

                    if line.code == 'RA':
                        data.update({'RA': line.total})
                    if line.code == 'RADED':
                        data.update({'RADED': line.total})
                    if line.code == 'RANET':
                        data.update({'RANET': line.total})

                    if line.code == 'CLANET':
                        data.update({'CLANET': line.total})

                    if line.code == 'FXDALW':
                        data.update({'FXDALW': line.total})
                    if line.code == 'FXDALWDED':
                        data.update({'FXDALWDED': line.total})
                    if line.code == 'FXDALWNET':
                        data.update({'FXDALWNET': line.total})
                    if line.code == 'OT':
                        data.update({'OT': line.total})
                    if line.code == 'OE':
                        data.update({'OE': line.total})
                    if line.code == 'LNDED':
                        loan_total = line.total
                        if loan_total:
                            loan_total = loan_total * -1
                        data.update({'LNDED': loan_total})
                    if line.code == 'OD':
                        od_total = line.total
                        if od_total:
                            od_total = od_total * -1
                        data.update({'OD': od_total})
                    if line.note:
                        data.update({'note': line.note})

                    if line.category_id.code == 'ALW':
                        total_allowance += line.total
                    if line.category_id.code == 'DED':
                        total_deduction += line.total

                    if line.code == 'GOSI':
                        gosi_value = line.total
                        if gosi_value:
                            gosi_value = gosi_value * -1
                        data.update({'GOSI': gosi_value})
                    if line.code == 'GROSS':
                        data.update({'GROSS': line.total})
                    if line.code == 'NET':
                        data.update({'NET': line.total})
                # Payslip Rules
                # If we activated other allowances or deductions we should
                # consider them here in the following equations.
                # TTLERNG = data['BNET'] + data['HANET'] + data['TANET'] \
                #           + data['CANET'] + data['RANET'] \
                #           + data['FXDALWNET'] + data['OE']
                TTLERNG = \
                    data['BNET'] + data['HANET'] \
                    + data['TANET'] + data['RANET'] + \
                    data['OE'] + data['CLANET']
                if not self.exclude_overtime:
                    TTLERNG += data['OT']
                ADED = total_deduction - data['BDED'] - data['HADED'] - \
                       data['TADED']
                if ADED:
                    ADED = ADED * -1
                if total_deduction:
                    total_deduction = total_deduction * -1
                data.update({

                    'TTLERNG': TTLERNG,
                    'TTLDED': data['GOSI'] + data['OD'] + data['LNDED'],
                    'ALW': total_allowance - data['HA'] - data['TA'],
                    'TDED': total_deduction,
                    'ADED': ADED
                })
                res.append(data)
        return res

    @api.model
    def set_line_data(self, slip_data_lst, worksheet):
        sheet_row = 5
        sheet_col = 0
        s7 = xlwt.easyxf('alignment: horizontal center')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        nationality = True if self.nationality else False
        cost_center = True if self.cost_center else False
        working_day = True if self.working_days else False
        hire_date = True if self.hiring_date else False
        salary_info = True if self.salary_information else False
        overtime = True if self.overtime else False
        net = True if self.net else False
        note = True if self.notes else False
        for slip_data in slip_data_lst:
            clm = 0
            worksheet.write(sheet_row, clm, label=slip_data['emp_id'])
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['name'])
            if nationality:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['country'])
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['job'])
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['dep'])
            if cost_center:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data[
                    'cost_center_id'])
            if working_day:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['work_days'])
            if hire_date:
                if slip_data['hire_date']:
                    clm += 1
                    worksheet.write(sheet_row, clm, datetime.strptime(
                        slip_data['hire_date'], DF), date_format)
                else:
                    clm += 1
                    worksheet.write(sheet_row, clm, '', style=s7)
            if salary_info:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['BASIC'],
                                style=s7)
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['HA'],
                                style=s7)
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['TA'],
                                style=s7)
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['RA'],
                                style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['BNET'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['HANET'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['TANET'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['RANET'], style=s7)
            if overtime:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['OT'],
                                style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['CLANET'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['OE'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['TTLERNG'],
                            style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['GOSI'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['LNDED'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['OD'], style=s7)
            clm += 1
            worksheet.write(sheet_row, clm, label=slip_data['TTLDED'],
                            style=s7)
            if net:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['NET'])
            if note:
                clm += 1
                worksheet.write(sheet_row, clm, label=slip_data['note'])
            sheet_col += 1
            sheet_row += 1
        return worksheet

    @api.model
    def _get_attachment(self, data):
        """
        create and return attachment
        :param data:
        :return:
        """
        today_date = DT.date.today()
        attachment_data = {
            'name': 'Employee_Payslips_' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas_fname': 'Payroll Report' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas': base64.encodestring(data),
            'res_model': '',
            'res_id': False,
            'mimetype': 'application/vnd.ms-excel'
        }
        attachment_rec = self.env['ir.attachment'].create(attachment_data)
        return attachment_rec

    @api.model
    def data_sorting(self, report_data):
        """
        sort data as per required
        :param report_data:
        :return:
        """
        data = report_data
        if self.sort_by == 'employee':
            data = sorted(report_data, key=lambda x: x['name'])
        if self.sort_by == 'department':
            data = sorted(report_data, key=lambda x: x['dep'])
        if self.sort_by == 'net':
            data = sorted(report_data, key=lambda x: x['NET'])
        # if self.sort_by == 'cost_center':
        #     sorted(report_data,
        #            key=lambda x: x['name'])
        return data

    @api.multi
    def print_payroll_report(self):
        # period_id = self._context.get('active_id', False)
        # if self.payrol_period_id:
        #     period_id = self.payrol_period_id.id
        start_date = self.date_from
        end_date = self.date_to
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Payroll Report')
        # Freeze row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(5)
        if not start_date or not end_date:
            raise Warning(_('You should select start and end date.'))
        self.set_header(worksheet, end_date)
        slip_data_lst = self._get_slip_details(start_date, end_date)
        if self.sort_by:
            slip_data_lst = self.data_sorting(slip_data_lst)
        self.set_line_data(slip_data_lst, worksheet)

        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['payroll.report.print.link'].create(
            {'name': 'Payroll Report.xls',
             'payroll_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class AttReportPringLink(models.Model):
    _name = 'payroll.report.print.link'

    payroll_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Payroll_Report.xls')
