# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Employee Customization',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
HR Employee Customization
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'base',
        'hr_contract',
        'resource',
        'hr_admin',
        'utm'
    ],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/hr_employee_view.xml',
        'views/hr_employee_menu_view.xml',
    ],
    'installable': True,
}
