# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Employment Status',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Employee's Employment Status
============================

Track the HR status of employees.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_recruitment',
        'hr_contract_state',
        'hr_employee_customization',
    ],
    'init_xml': [
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/templates.xml',
        'views/hr_employee_data.xml',
        'views/hr_view.xml',
        'views/end_contract_view.xml',
        'views/email_notification_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
