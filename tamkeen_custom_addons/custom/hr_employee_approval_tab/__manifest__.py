# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Approval/Delegation Tab',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Employee Approval/Delegation Tab
    """,
    'author': 'Bista Solutions',
    'depends': [
        'hr',
        'hr_employee_customization',
    ],
    'data': [
        'security/hr_security.xml',
        'views/hr_view.xml',
    ],
    'installable': True,
    'active': False,
}
