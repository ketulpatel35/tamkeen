# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Contracts - Initial Settings',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Initial Settings on New Contracts
========================================
    - Starting Wages
    - Salary Structure
    - Trial Period Length
    """,
    'author': 'bistasolutions.com',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr',
        'hr_contract',
        'hr_job_categories',
        'hr_payroll',
        'hr_admin',
        'hr_employee_customization',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/hr_contract_view.xml',
    ],
    'installable': True,
    'active': False,
}
