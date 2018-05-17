# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Order ESS',
    'version': '1.1',
    'category': 'Purchase Management',
    'depends': ['purchase_config', 'emp_self_services'],
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'description': """
    Purchase Order ESS
    """,
    'data': [
        'views/purchase_order_view.xml',
        'views/purchase_order_menu.xml'
    ],
    'installable': True,
    'auto_install': False
}
