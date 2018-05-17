# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Period',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Easy Payroll Management
=======================
This module implements a more formal payroll cycle. This cycle is based on
payroll
period schedules configured by the user. An end-of-pay-period wizard guides the
HR officer or manager through the payroll process. For each payroll period a
specific set
of criteria have to be met in order to proceed to the next stage of the
process. For
example:
    - Attendance records are complete
    """,
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr_payroll',
        'hr_payroll_register',
        'hr_payslip_amendment',
        'web_readonly_bypass',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_period_data.xml',
        'views/hr_payroll_period_view.xml',
        'views/hr_payroll_period_cron.xml',
        'views/report.xml',
        'views/report_hr_payroll_bank_transfer.xml',
        'report/payroll_report_view.xml',
        'wizard/payroll_report_wizard_view.xml',
        'wizard/payroll_period_end_view.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
