# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Grade Level in Employee',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
    This Module Add Grade Level in Employee
    """,
    'author': 'Bistasolutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_contract_grade_level',
        'org_structure_payroll',

    ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'active': False,
}
