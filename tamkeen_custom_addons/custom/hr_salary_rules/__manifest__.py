# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Salary Rules',
    'version': '1.0',
    'category': 'HR',
    'description': """
HR Salary Ruls
        """,
    'author': 'Tamkeen Tech',
    'website': 'https://www.open-inside.com',
    'depends': [
            'hr_payroll',
            'hr_payslip_addtion',
    ],
    'data': [
        'salary_rules_data.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
