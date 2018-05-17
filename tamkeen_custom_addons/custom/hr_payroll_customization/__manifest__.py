# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Customization',
    'category': 'Payroll',
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'version': '1.0',
    'description': """
    Payroll Customization
    """,
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll_view.xml'
    ],
    'active': True,
    'installable': True,
}
