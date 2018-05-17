# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Employee New View',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': ['emp_self_services', 'hr_employee_marked_roles', 'hr_skill', 'hr_saudi_filed'],
    'data': [
            'views/hr_employee_view.xml',
            'views/team_members_menu.xml'
        ],
    'installable': True,
    'auto_install': False,
}
