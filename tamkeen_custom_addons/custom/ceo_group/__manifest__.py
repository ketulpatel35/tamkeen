# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'CEO Group',
    "version": "0.1",
    'depends': ['account',
                'project', 'stock',
                'hr_admin',
                'sales_team',
                'purchase',
                'survey',
                'emp_self_services',
                ],
    "license": "AGPL-3",
    "author": "Bista Solutions",
    "website": "http://www.bistasolutions.com",
    'description': """
    """,
    'data': [
        'views/ir_ui_menu_view.xml',
        'security/ir_rule.xml',
        'views/purchase_view.xml',
        'views/emp_self_services_view.xml',
    ],
    "demo": [],
    "test": [],
    'installable': True,
    'auto_install': False,
    "images": [],
}
