# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Register',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Payroll Register
================
    - Process payslips by department
    """,
    'author': 'Bista solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        # 'hr_accrual',
        # 'hr_policy_accrual',
        'hr_payroll_customization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hr_payroll_register_run_view.xml',
        'views/hr_payroll_register_view.xml',
        'views/hr_payroll_register_report.xml',
        'report/report_payslips_template_view.xml',
        'report/report_payroll_summary_template_view.xml',
        'report/report_payslip_summary.xml',
    ],
    'installable': True,
    'active': False,
}
