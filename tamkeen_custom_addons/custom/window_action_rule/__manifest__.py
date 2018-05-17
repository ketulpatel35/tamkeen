# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Window Actions Rules',
    'version': '1.0',
    'category': 'Web',
    'sequence': 1,
    'summary': 'Window Actions Rules',
    'description': """Window Actions Rules Restriction""",
    'author': 'Bista Soutions',
    'website': '',
    'depends': ['base', 'hr'],
    'data': [
        'security/window_actions_security.xml',
        'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
