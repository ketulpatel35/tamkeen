# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Payslip Amendment',
    'version': '1.0',
    'category': 'Generic Modules/Company Data',
    'author': 'Bista Solutions',
    'description': """
Add Amendments to Current and Future Pay Slips
==============================================
    """,
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr_payroll',
        'hr_payslip_amendment',
        'hr_payroll_period'
    ],
    'data': [
        'wizard/hr_payroll_payslips_by_employees_views.xml',
        'views/hr_payroll_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
