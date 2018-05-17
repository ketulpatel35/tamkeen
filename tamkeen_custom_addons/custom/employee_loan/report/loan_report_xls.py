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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class HrLoanManagementXLS(models.TransientModel):
    _name = 'loan.management.report.xls'

    date_from = fields.Date(string='Date From',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To')

    sort_by = fields.Selection([('employee', 'Employee'),
                                ('department', 'Department'),
                                ('cost_center', 'Cost Center')],
                               string='Sort By')

    is_request_number = fields.Boolean(string='Request Number', default=True)
    is_loan_amount = fields.Boolean(string='Loan Amount', default=True)
    is_paid_installments_amount = fields.Boolean(
        string='Paid Installments Amount', default=True)
    is_emp_performance_evaluation = fields.Boolean(
        string='Employee Performance Evaluation', default=True)
    is_cost_center = fields.Boolean(string='Cost Center', default=True)
    is_loan_installments_number = fields.Boolean(
        string='Loan Installments Number', default=True)
    is_remaining_amount = fields.Boolean(string='Remaining Amount',
                                         default=True)
    is_status = fields.Boolean(string='Status', default=True)

    employee_ids = fields.Many2many('hr.employee',
                                    'loan_report_employee_rel',
                                    'report_id', 'emp_id', string='Employees')
    cost_center_ids = fields.Many2many('account.analytic.account',
                                       'loan_report_cost_center_rel',
                                       'report_id', 'cost_center_id',
                                       string='Cost Center')
    stage_ids = fields.Many2many('service.panel.displayed.states',
                                 string='Status',
                                 domain="[('model_id.model', '=', "
                                        "'hr.employee.loan')]")

    @api.onchange('date_from')
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
                raise Warning(_('Date from must be earlier than Date to.'))
            if self.date_to > add_days_from_strf:
                self.date_to = add_days_from_strf

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
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        s3 = xlwt.easyxf(
            'font: bold 1, height 260, colour h1_text_color;'
            'alignment: horizontal center, wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour gray40,'
            'fore_colour gray40')
        header_0 = "Loan Installments Report for the Period From %s to %s" %\
                   (str(self.date_from), str(self.date_to))
        header_1 = "Loan Information"
        worksheet.write_merge(0, 0, 0, 4, header_0, s1)
        worksheet.write_merge(0, 0, 5, 12, header_1, s3)
        worksheet.write_merge(1, 1, 0, 0, 'Employee Name', s2)
        worksheet.write_merge(1, 1, 1, 1, 'Employee Company ID', s2)
        worksheet.write_merge(1, 1, 2, 2, 'Department', s2)
        worksheet.write_merge(1, 1, 3, 3, 'Position', s2)
        worksheet.write_merge(1, 1, 4, 4, 'Hiring Date', s2)
        label_lst = []
        if self.is_request_number:
            label_lst.append('Request Number')
        if self.is_cost_center:
            label_lst.append('Cost Center')
        if self.is_loan_amount:
            label_lst.append('Loan Amount')
        if self.is_loan_installments_number:
            label_lst.append('Loan Installments Number')
        if self.is_paid_installments_amount:
            label_lst.append('Paid Installments Amount')
        if self.is_remaining_amount:
            label_lst.append('Remaining Amount')
        if self.is_status:
            label_lst.append('Status')
        if self.is_emp_performance_evaluation:
            label_lst.append('Employee Performance Evaluation')
        column_count = 5
        for label in label_lst:
            worksheet.write(1, column_count, label, s2)
            column_count += 1

    @api.model
    def get_loan_report_line(self):
        """
        get loan report line
        :return:
        """
        data = []
        domain = []
        f_date = datetime.strptime(self.date_from,
                                   DEFAULT_SERVER_DATE_FORMAT).date()
        e_date = datetime.strptime(self.date_to,
                                   DEFAULT_SERVER_DATE_FORMAT).date()
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.cost_center_ids:
            domain.append(('cost_center_id', 'in', self.cost_center_ids.ids))
        if self.stage_ids:
            domain.append(('stage_id', 'in', self.stage_ids.ids))
        for loan_rec in self.env['hr.employee.loan'].search(domain):
            c_date = datetime.strptime(loan_rec.create_date,
                                       OE_DTFORMAT).date()
            if f_date <= c_date <= e_date:
                data.append({'emp_name': loan_rec.employee_id.name,
                             'company_id': loan_rec.employee_id.f_employee_no,
                             'department': loan_rec.employee_id.department_id.name,
                             'position': loan_rec.employee_id.job_id.name,
                             'hiring_date':
                                 loan_rec.employee_id.initial_employment_date,
                             'request_name': loan_rec.name,
                             'cost_center': loan_rec.cost_center_id.name,
                             'loan_amount': loan_rec.loan_amount,
                             'inst_number': loan_rec.installment_number,
                             'paid_installment':
                                 loan_rec.total_paid_installment_amount,
                             'remaining_installments':
                                 loan_rec.remaining_installments_total_amount,
                             'status': loan_rec.stage_id.name,
                             'evaluation': loan_rec.employee_performance_evaluation
                             })
        return data

    @api.model
    def set_line_data(self, worksheet):
        """
        set line in excel report
        :param worksheet: excel object
        :return:
        """
        line_items = self.get_loan_report_line()
        if self.sort_by:
            if self.sort_by == 'cost_center':
                line_items = sorted(line_items,
                                     key=lambda x: x['cost_center'])
            if self.sort_by == 'employee':
                line_items = sorted(line_items,
                                     key=lambda x: x['emp_name'])
            if self.sort_by == 'department':
                line_items = sorted(line_items,
                                     key=lambda x: x['department'])
        row_count = 2
        for line in line_items:
            column_count = 0
            worksheet.write(row_count, column_count, line.get('emp_name', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('company_id', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('department',
                                                              ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('position', ''))
            column_count += 1
            worksheet.write(row_count, column_count, line.get('hiring_date',
                                                              ''))
            column_count += 1
            if self.is_request_number:
                worksheet.write(row_count, column_count, line.get(
                    'request_name', ''))
                column_count += 1
            if self.is_cost_center:
                worksheet.write(row_count, column_count,
                                line.get('cost_center', ''))
                column_count += 1
            if self.is_loan_amount:
                worksheet.write(row_count, column_count,
                                line.get('loan_amount', ''))
                column_count += 1
            if self.is_loan_installments_number:
                worksheet.write(row_count, column_count,
                                line.get('inst_number', ''))
                column_count += 1
            if self.is_paid_installments_amount:
                worksheet.write(row_count, column_count,
                                line.get('paid_installment', ''))
                column_count += 1
            if self.is_remaining_amount:
                worksheet.write(row_count, column_count,
                                line.get('remaining_installments', ''))
                column_count += 1
            if self.is_status:
                worksheet.write(row_count, column_count,
                                line.get('status', ''))
                column_count += 1
            if self.is_emp_performance_evaluation:
                worksheet.write(row_count, column_count,
                                line.get('evaluation', ''))
                column_count += 1
            row_count += 1

    @api.multi
    def print_loan_report(self):
        """
       Loan xls Report
       :return: {}
       """
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Loan Management Report')
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 160, 122)
        xlwt.add_palette_colour("h1_text_color", 0x22)
        workbook.set_colour_RGB(0x22, 204, 51, 0)
        xlwt.add_palette_colour("h2_text_color", 0x23)
        workbook.set_colour_RGB(0x23, 128, 25, 0)
        self.set_header(worksheet)
        self.set_line_data(worksheet)
        # Freeze column,row
        worksheet.set_panes_frozen(True)
        worksheet.set_horz_split_pos(2)
        worksheet.set_vert_split_pos(5)
        stream = StringIO()
        workbook.save(stream)
        attach_id = self.env['loan.report.print.link'].create(
            {'name': 'Loan Report.xls',
             'loan_xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class LoanReportPrintLink(models.Model):
    _name = 'loan.report.print.link'

    loan_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Loan_Report.xls')
