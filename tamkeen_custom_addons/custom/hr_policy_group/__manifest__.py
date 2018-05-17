# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Human Resources Policy Groups',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
HR Policy Groups
================

Define a collection of policies, such as Overtime, that apply to a contract.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_contract',
        'hr_contract_init',
        'hr_admin',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_policy_group_view.xml',
    ],
    'installable': True,
    'active': False,
}
