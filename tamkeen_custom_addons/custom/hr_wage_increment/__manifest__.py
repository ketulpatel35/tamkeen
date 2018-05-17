# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "HR Wage Increment",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
Wage Increment Handling
=======================

    This module provides a way to handle wage increments that automatically
    creates a
    new contract for the rest of the duration of the employee's current
    contract with the new amount.
    """,
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    "depends": [
        # "hr_payroll_period",
        "hr_admin",
        "hr_contract_state"
    ],
    "init_xml": [],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/wage_adjustment_by_employees.xml',
        'views/wage_increment_view.xml',
        'views/hr_contract_view.xml',
    ],
    'installable': True,
    'active': False,
}
