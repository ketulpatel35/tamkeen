# -*- coding:utf-8 -*-
# import time
from datetime import datetime as dat
from odoo.tools.translate import _
from odoo import api, fields, models


class HrPayrollRegister(models.Model):
    _name = 'hr.payroll.register'

    @api.model
    def _get_default_name(self):
        """
        set default name
        :return:
        """
        nMonth = dat.now().strftime('%B')
        year = dat.now().year
        name = _('Payroll for the Month of %s %s' % (nMonth, year))
        return name

    @api.model
    def _get_company(self):
        """
        set default company
        :return:
        """
        users_pool = self.env['res.users']
        return users_pool.browse(self._uid)[0].company_id.id

    name = fields.Char(string='Description',
                       default=_get_default_name)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close')],
        string='Status',
        readonly=True,
        default='draft')
    date_start = fields.Datetime('Date From')
    date_end = fields.Datetime('Date To')
    run_ids = fields.One2many('hr.payslip.run',
                              'register_id')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=_get_company)

    _sql_constraints = [('unique_name', 'UNIQUE(name)',
                         _('Payroll Register description must be unique.'))]

    @api.multi
    def action_delete_runs(self):
        """
        remove genarated employee payslip
        :return:
        """
        hr_payslip_run_obj = self.env['hr.payslip.run']
        hr_payslip_run_rec = hr_payslip_run_obj.search([
            ('register_id', 'in', self._ids)])
        if hr_payslip_run_rec:
            hr_payslip_run_rec.unlink()
        return True

    @api.multi
    def get_payroll_details(self):
        """
        get list of dictionary of the payslip of employee that is being
        generated for a specific month.
        :return:
        """
        vals = []
        for dept in self.mapped('run_ids'):
            for emp in dept.mapped('slip_ids'):
                emp_name = emp.employee_id.name
                vals.append(
                    {
                        'emp_id': emp.employee_id.f_employee_no,
                        'emp_name': emp.employee_id.name,
                        'nationality': emp.employee_id.country_id.name,
                        'job_name': emp.employee_id.job_id.name,
                        'department': emp.employee_id.department_id.name,
                        # 'cost_center':,
                        'working_days': {'work_day': 0.00},
                        'hier_date': emp.employee_id.initial_employment_date,
                        'salary':
                            {
                                'Basic': 0.00,
                                'Housing': 0.00,
                                'Transportation': 0.00,
                                'Cashier_Allowance': 0.00,
                                'Rare_Allowance': 0.00,
                                'Fixed_Allowance': 0.00,
                                'Other_Earnings': 0.00,
                                'Total_Earnings': 0.00,
                                'GOSI': 0.00,
                                'Other_Deduction': 0.00,
                                'Total_Deduction': 0.00,
                                'Total_Net': 0.00,
                        },
                    })

                for work in vals:
                    if work['emp_name'] == emp_name:
                        for workdays in emp.mapped('worked_days_line_ids'):
                            work['working_days'][
                                'work_day'] = workdays.number_of_days

                for salary in vals:
                    if salary['emp_name'] == emp_name:
                        for salary_info in emp.mapped('line_ids'):
                            if salary_info.code == 'BASIC':
                                salary['salary']['Basic'] = salary_info.total
                            if salary_info.code == 'HA':
                                salary['salary']['Housing'] = salary_info.total
                            if salary_info.code == 'TA':
                                salary['salary'][
                                    'Transportation'] = salary_info.total
                            if salary_info.code == 'CA':
                                salary['salary'][
                                    'Cashier_Allowance'] = salary_info.total
                            if salary_info.code == 'RA':
                                salary['salary'][
                                    'Rare_Allowance'] = salary_info.total
                            if salary_info.code == 'FXDALW':
                                salary['salary'][
                                    'Fixed_Allowance'] = salary_info.total
                            if salary_info.code == 'OE':
                                salary['salary'][
                                    'Other_Earnings'] = salary_info.total
                            if salary_info.code == 'GOSI':
                                salary['salary']['GOSI'] = salary_info.total
                            if salary_info.code == 'OD':
                                salary['salary'][
                                    'Other_Deduction'] = salary_info.total

                            salary['salary']['Total_Earnings'] = \
                                salary['salary']['Basic'] + \
                                salary['salary']['Housing'] + \
                                salary['salary']['Transportation'] + \
                                salary['salary']['Cashier_Allowance'] + \
                                salary['salary']['Rare_Allowance'] + \
                                salary['salary']['Fixed_Allowance'] + \
                                salary['salary']['Other_Earnings']

                            salary['salary']['Total_Deduction'] = \
                                salary['salary']['GOSI'] + \
                                salary['salary']['Other_Deduction']

                            salary['salary']['Total_Net'] = salary['salary'][
                                'Total_Earnings'] - \
                                salary['salary'][
                                'Total_Deduction']
        return vals


class HrPayrollRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = 'hr.payslip.run'

    register_id = fields.Many2one('hr.payroll.register', string='Register')
