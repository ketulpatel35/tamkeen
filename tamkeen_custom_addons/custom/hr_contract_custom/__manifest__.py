# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{"name": "HR Contract Custom",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
HR Contract Reference
=====================
This module provides :
    - Unique reference number for each employee contract
    - Automatically generated
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    "depends": ['hr_contract', 'hr_payroll', 'hr_salary_rules',
                'hr_payroll_account'],
    'data': [
        'hr_contract_view.xml',
        'hr_contract_sequence.xml',
        'salary_rules_data.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
 }
