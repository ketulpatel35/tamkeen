# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "HR Permission Groups",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
Human Resource Permission Groups
================================

    """,
    "author": "bistasolutions.com",
    "website": "http://bistasolutions.com",
    "depends": [
        'base',
        'hr',
        # 'hr_admin'
        # 'hr_payroll',
        # 'hr_contract',
        # 'hr_payslip_amendment',
    ],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
