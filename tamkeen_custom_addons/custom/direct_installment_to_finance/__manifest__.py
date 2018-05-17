# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Direct Installment to Finance',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Loan Management',
    'description': """
    Employee Paid to Cash for Loan.
""",
    'depends': [
        'account',
        'employee_loan'
    ],
    'data': [
        'views/employee_cash_installment.xml'
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
