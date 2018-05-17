# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Grade Level in Contract',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
    This Module Add Grade Level in contract
    """,
    'author': 'Bistasolutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_contract',
        'hr',
        'hr_admin',
        'hr_contract_init',
        # 'hr_contract_state'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_view.xml',
    ],
    'installable': True,
    'active': False,
}
