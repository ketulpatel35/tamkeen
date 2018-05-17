# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Payroll addition',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 100,
    'category': 'Human Resources',
    'website': 'http://www.bistasolutions.com',
    'summary': 'payroll',
    'description': """
HR Payroll
""",
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'hr_payslip_view.xml',
    ],
    'images': [],

    'demo': [],

    'installable': True,
    'application': True,
}
