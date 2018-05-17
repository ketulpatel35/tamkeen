# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Org Shift Management',
    'version': '1.1',
    'author': 'Bista Solutions',
    'category': 'Shift Management',
    'description': """
    """,
    'depends': ['hr_schedule', 'organization_structure', 'hr_public_holidays'],
    'data': [
        'views/hr_schedule_template_view.xml',
        'views/menu_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
