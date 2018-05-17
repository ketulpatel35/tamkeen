# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Update Information',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Employee Update Info.',
    'description': """
Employee can Update his/her Information based on particular group.
""",
    'depends': [
        'base', 'hr', 'hr_contract', 'hr_saudi_filed', 'hr_employee_customization',
        'hr_employee_id', 'emp_self_services', 'hr_employee_marked_roles'
    ],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_info.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
