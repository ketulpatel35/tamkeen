# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Time Accrual Policy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Time Accrual Policies
============================
Define properties of a leave accrual policy. The accrued time is calculated
based on the length of service of the employee. An additional premium may be
added on the base rate based on additional months of service. This policy
isvideal
for annual leave accruals. If the type of accrual is 'Standard' time is
accrued and
withdrawn manually. However, if the type is 'Calendar' the time is accrued (
and recorded)
at a fixed frequency.
    """,
    "author": "bistasolutions.com",
    "website": "http://bistasolutions.com",
    'depends': [
        'hr_accrual',
        # 'hr_contract_state',
        'hr_employee_customization',
        'hr_policy_group',
        'hr_holidays',
    ],
    'init_xml': [
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_policy_accrual_cron.xml',
        'views/hr_policy_accrual_view.xml',
        'views/hr_holidays_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
