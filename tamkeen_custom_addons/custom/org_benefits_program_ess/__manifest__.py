# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Benefits Program ESS',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Benefits Program ESS',
    'description': """
    - Benefits Program Request
    - Employee Self Service
    - Management Approvals
    - Manager Dashboard
""",
    'depends': ['org_benefits_program', 'hr_dashboard'],
    'data': [
        'views/org_benefits_program_view.xml',
        'views/org_benefits_program_menu_view.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
