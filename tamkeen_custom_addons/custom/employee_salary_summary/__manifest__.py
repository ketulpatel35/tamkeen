# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Salary Summary',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Employee Salary Summary Report ',
    'description': """
   This module allow to print report of employee salary summary
""",
    'depends': [
        'hr','org_levels_indexing','hr_employee_id',
        'org_structure_analytic_account'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/employee_salary_summary_view.xml',

    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
