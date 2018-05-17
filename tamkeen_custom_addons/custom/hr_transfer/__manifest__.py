# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Departmental Transfer',
    'version': '1.0',
    'category': 'Localization',
    'description': """
Transfer Employees between Departments
======================================

    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_contract',
        'hr_wage_increment'
    ],
    'init_xml': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'hr_transfer_cron.xml',
        'hr_transfer_data.xml',
        'hr_transfer_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
