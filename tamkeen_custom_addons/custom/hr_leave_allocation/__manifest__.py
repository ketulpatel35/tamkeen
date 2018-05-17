# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'HR Leave Allocation',
    'version': '1.0',
    'author': 'Bista Solutions',
    'category': 'HR/Leave',
    'website': '',
    'summary': 'HR Leave Balance',
    'description': """
HR Leave Balance:
=========================================
- Add the employee leave balance
 in his/her contract to be visible by the authorized persons only.
""",
    'depends': [
        'hr',
        'hr_holidays_extension',
    ],
    'data': [
        # 'security/user_groups.xml',
        'security/ir.model.access.csv',
        'wizard/hr_allocation_leave_wizard.xml',
        'views/hr_leave_allocation_view.xml',
        'views/hr_holidays_view.xml',
        'views/res_company_view.xml',
        'views/menu_view.xml',
    ],
    'images': [],
    'update_xml': [],
    'demo': [],
    'installable': True,
    'application': True,
}
