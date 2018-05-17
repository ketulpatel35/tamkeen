# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Recruitment Employee Self Service",
    'summary': 'Recruitment Employee Self Service',
    'description': """
Recruitment Employee Self Service
==========================
Recruitment Employee Self Service Dashboard.
    """,
    'category': 'HR',
    'version': '1.0',
    'depends': [
        'base',
        'hr_recruitment_stages_movement',
        'hr_dashboard',
    ],
    # Views templates, pages, menus, options and snippets
    'data': [
        'views/manager_dashboard_load.xml',
    ],
    # Qweb templates
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    # Your information
    'author': 'Bistasolutions.com',
    'maintainer': 'bistasolutions.com',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    # Technical options
    'demo': [],
    'test': [],
    'installable': True,
    # 'auto_install':False,
    # 'active':True,
}
