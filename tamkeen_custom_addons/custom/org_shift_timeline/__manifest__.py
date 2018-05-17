# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Org Shift Timeline',
    'version': '1.1',
    'author': 'Bista Solutions',
    'category': 'Shift Timeline',
    'description': """
    """,
    'depends': ['hr',
                'org_resource_calendar',
                'organization_structure', 'mail'
                ],
    'data': [
        'views/org_shift_management_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/menu_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
