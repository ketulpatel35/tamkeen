# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Payroll/Salary Rules',
    'version': '1.0',
    'category': 'Payroll',
    'description': """
Payroll Register
================
    """,
    'author': 'Bista solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_payroll'
    ],
    'data': [
        'views/salary_rule_to_be_display_view.xml'
    ],
    'installable': True,
    'active': False,
}
