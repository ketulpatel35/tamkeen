# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Manage Employee Contracts',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Employee Contract Workflow and Notifications
============================================

Easily find and keep track of employees who are nearing the end of their
contracts and
trial periods.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_contract',
        'hr_contract_init',
        # 'hr_employee_state'
    ],
    'init_xml': [
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_contract_cron.xml',
        'views/hr_contract_data.xml',
        'views/hr_contract_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
