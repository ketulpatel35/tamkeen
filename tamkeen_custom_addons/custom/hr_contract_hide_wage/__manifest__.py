# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Hide Wage',
    'version': '1.0',
    'category': 'hr',
    'description': """
    """,
    'author': 'bistasolutions.com',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr',
        'hr_contract',
        'hr_contract_init',
    ],
    'data': [
        'security/user_groups.xml',
        'views/hr_contract_view.xml',
    ],
    'installable': True,
    'active': False,
}
