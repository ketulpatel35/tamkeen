# -*- coding:utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning


class PrintPayrollRegister(models.TransientModel):
    _name = 'print.payroll.report.wiz'
    _description = 'Print Payroll Register'

    is_payroll_register_report = fields.Boolean('Payroll Register Report')
    is_payslip_details_report = fields.Boolean('Payslip Details Report')
    is_summary_report = fields.Boolean('Summary Report')
    payroll_period_id = fields.Many2one('hr.payroll.period',
                                        string='Payroll Period')
    report_format = fields.Selection([('pdf', 'PDF report'),
                                      ('xls', 'XLS Report')], default='xls')
    date_start = fields.Datetime(string='Period Start Date')
    date_end = fields.Datetime(string='Period End Date')
    # department_ids = fields.Many2many('hr.department', 'payroll_rept_dept_rel',
    #                                   'p_id', 'd_id', string="Departments")

    # is_parent_dept = fields.Boolean('Parent Department', default=True)
    is_cost_center = fields.Boolean('Cost Center', default=True)
    is_basic = fields.Boolean('Basic', default=True)
    is_transport_allowance = fields.Boolean('Transport Allowance',
                                            default=True)
    is_housing_allowance = fields.Boolean('Housing Allowance', default=True)
    is_rate_allowance = fields.Boolean('Rare Allowance',default=True)
    is_other_earnings = fields.Boolean('Other Earnings', default=True)
    is_other_allowances = fields.Boolean("Total Earnings", default=True)
    is_gosi_deduction = fields.Boolean("GOSI Deduction", default=True)
    is_other_deductions = fields.Boolean('Other Deductions', default=True)
    is_total_deductions = fields.Boolean("Total Deductions", default=True)
    is_total_gross = fields.Boolean('Total Gross', default=True)
    is_total_net_salary = fields.Boolean('Total Net Salary', default=True)
    is_has_no_child = fields.Boolean('Department has no Child/s', default=True)
    is_cost_of_living_allowance = fields.Boolean(string='Cost of Living '
                                                        'Allowance',
                                                 default=True)

    @api.onchange('payroll_period_id')
    def onchange_payroll_period_id(self):
        """
        :return:
        """
        if self.is_summary_report and self.payroll_period_id:
            self.date_start = self.payroll_period_id.date_start
            self.date_end = self.payroll_period_id.date_end

    @api.model
    def default_get(self, fields):
        """
        set default payroll period id.
        :param fields:
        :return:
        """
        res = super(PrintPayrollRegister, self).default_get(fields)
        today_date = datetime.today()
        first_date_of_month = today_date.replace(day=1)
        lastMonth_date = first_date_of_month - timedelta(days=1)
        payroll_period_obj = self.env['hr.payroll.period']
        payroll_period_rec = payroll_period_obj.search([
            ('state', 'in', ('open', 'ended')),
            ('date_start', '>=', str(lastMonth_date))],
            order="date_start", limit=1)
        if payroll_period_rec:
            res['payroll_period_id'] = payroll_period_rec.id
        return res

    @api.multi
    def print_report(self):
        """
        print report
        :return:
        """
        # Payslip Template
        period_rec = self.payroll_period_id
        if self.is_payroll_register_report:
            if not period_rec.register_id:
                raise Warning(_('There are no related payslip/s generated '
                                'for the selected payroll period.'))
            return self.env['report'].get_action(
                period_rec.register_id,
                'hr_payroll_register.report_payslips_template')
        # Payslip Details
        if self.is_payslip_details_report:
            slip_ids = []
            for run in period_rec.register_id.run_ids:
                [slip_ids.append(s.id) for s in run.slip_ids]
            return self.env['report'].get_action(slip_ids,
                                                 'hr_payroll.report_payslip')
        # Summary Report
        if self.is_summary_report:
            if not period_rec.register_id:
                raise Warning(_('There are no related payslip/s generated '
                                'for the selected payroll period.'))
            return self.env['report'].get_action(
                period_rec.register_id,
                'hr_payroll_register.report_payroll_summary_template')

    @api.multi
    def print_xls_report(self):
        """
        print XLS report
        :return:
        """
        # WRITE CODE FOR XLS REPORT ...
        summary_xls = self.env['payslip.summary.report.xls']
        # department_ids = []
        # if self.department_ids:
        #     department_ids = self.department_ids.ids
        fields_to_display = ['is_cost_center', 'is_basic',
                             'is_transport_allowance',
                             'is_housing_allowance', 'is_rate_allowance',
                             'is_other_earnings', 'is_other_allowances',
                             'is_gosi_deduction', 'is_other_deductions',
                             'is_total_deductions', 'is_total_gross',
                             'is_total_net_salary', 'is_has_no_child', 'is_cost_of_living_allowance']
        if not self.is_cost_center:
            fields_to_display.remove('is_cost_center')
        if not self.is_basic:
            fields_to_display.remove('is_basic')
        if not self.is_transport_allowance:
            fields_to_display.remove('is_transport_allowance')
        if not self.is_housing_allowance:
            fields_to_display.remove('is_housing_allowance')
        if not self.is_rate_allowance:
            fields_to_display.remove('is_rate_allowance')
        if not self.is_other_earnings:
            fields_to_display.remove('is_other_earnings')
        if not self.is_other_allowances:
            fields_to_display.remove('is_other_allowances')
        if not self.is_gosi_deduction:
            fields_to_display.remove('is_gosi_deduction')
        if not self.is_other_deductions:
            fields_to_display.remove('is_other_deductions')
        if not self.is_total_deductions:
            fields_to_display.remove('is_total_deductions')
        if not self.is_total_gross:
            fields_to_display.remove('is_total_gross')
        if not self.is_total_net_salary:
            fields_to_display.remove('is_total_net_salary')
        if not self.is_has_no_child:
            fields_to_display.remove('is_has_no_child')
        if not self.is_cost_of_living_allowance:
            fields_to_display.remove('is_cost_of_living_allowance')
        get_data = summary_xls.print_payslip_summary_xls_report(
            self.payroll_period_id, fields_to_display)
        return get_data
