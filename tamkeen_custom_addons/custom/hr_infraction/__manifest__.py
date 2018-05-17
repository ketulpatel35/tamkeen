# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Infraction Management',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Warning/Disciplinary Action Management
========================================
    """,
    'author': 'Bista solutions',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr',
        # 'hr_employee_state',
        # 'hr_admin',
        # 'hr_transfer',
        # 'hr_employee_customization',
    ],
    'init_xml': [
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/action.xml',
        'views/hr_infraction_data.xml',
        'views/hr_infraction_view.xml',
        'security/ir_rule.xml'
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
