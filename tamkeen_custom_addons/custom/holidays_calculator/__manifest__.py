# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Holidays Calculator",
    "version": "1.0",
    "author": "Bistasolutions",
    "category": 'Human Resources/Leaves',
    "description": """
    * Help the HR Officer to
    allocate an initial
    leave balance to
    the new joiners.

    * Display all the
    selected employee's
    leave information.
    """,
    'website': 'http://www.bistasolutions.com/',
    "depends": ['hr_contract', 'hr_holidays', 'hr_employee_customization'],
    'data': [
        'security/hr_security.xml',
        # 'security/ir.model.access.csv',
        'wizard/hr_holidays_calculator_view.xml',
        # 'views/calculator.xml'
    ],
    'installable': True,
    'active': False,
}
