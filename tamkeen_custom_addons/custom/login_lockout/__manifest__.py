# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Lockout Mechanism',
    'version': '0.1',
    'category': 'Tools',
    'description': """
    - Implements the lockout Mechanism.
""",
    'author': 'Bista solutions',
    'website': 'http://bistasolutions.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_user_view.xml',
        'views/login_attempt_config_view.xml',
        'views/login_attempt_view.xml',
        'views/module_menus.xml',
    ],
    # i can not find static/src/js/login_lockout.js  so i had removed from js
    'js': [],
    'installable': True,
    'active': False,
}
