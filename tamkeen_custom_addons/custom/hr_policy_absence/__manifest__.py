# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Absence Policy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Absence Policies
========================
Define properties of an absence policy, such as:
    * Type (paid, unpaid)
    * Rate (multiplier of base wage)
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_payroll',
        'hr_holidays',
        'hr_admin',
        # 'hr_payroll_period',
        'hr_policy_group',
    ],
    'init_xml': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/leave_types.xml',
        'data/salary_rules_data.xml',
        'hr_policy_absence_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
