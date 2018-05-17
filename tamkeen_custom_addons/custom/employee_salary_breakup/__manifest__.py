# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Salary Breakup',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Employee Salary Breakup ',
    'description': """
   Employee Salary Breakup
""",
    'depends': [
        'hr', 'hr_contract', 'hr_contract_init'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_view.xml'
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
