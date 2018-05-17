# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'Employee Remaining Leave Balance',
    'version': '1.0',
    'author': 'Tamkeen ERP Team',
    'sequence': 17,
    'category': 'HR/Leave',
    'website': '',
    'summary': 'Remaining Leave Balance',
    'description': """
Remaining Leave Balance Calculation:
=========================================
- Add the remaining employee leave balance
 in his/her contract to be visible by the authorized persons only.
- This module depend on the future leave balance calculation.
""",
    'depends': [
        'hr',
        'employee_leave_summary',
        'hr_holidays_extension',
    ],
    'data': [
        'views/remaining_leave_balance_view.xml',
    ],
    'images': [],
    'update_xml': [],
    'demo': [],
    'installable': True,
    'application': True,
}
