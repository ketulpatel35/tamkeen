# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Invoice Validation',
    'version': '1.1',
    'category': 'Purchase Management',
    'depends': ['purchase', 'invoice_extension'],
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'description': """
    Allowed to Invoice more then the Purchase Order Amount
    """,
    'data': [
        'views/purchase_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
