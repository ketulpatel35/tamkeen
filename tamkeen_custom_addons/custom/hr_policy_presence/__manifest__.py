# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Employee Presence Policy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Employee Presence Policies
=================================
Define properties of an employee presence policy, such as:
    * The number of regular working hours in a day
    * The maximum possible hours
    * Rate (multiplier of base wage)
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_policy_group',
        'hr_admin',
    ],
    'init_xml': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'hr_policy_presence_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
