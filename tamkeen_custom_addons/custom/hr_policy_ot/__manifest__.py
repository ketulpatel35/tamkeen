# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Overtime Policy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Overtime Policies
========================
Define properties of an overtime policy, such as:
    * Type (daily, weekly, or holiday)
    * Rate (multiplier of base wage)
    * Active Hours
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
        'hr_policy_ot_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
