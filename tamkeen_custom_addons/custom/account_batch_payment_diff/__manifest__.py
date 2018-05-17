# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Batch Payment Diffrence',
    'version': '0.1',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'description': """
    - Enable Batch invoice payment with write off
    """,
    'depends': [
        'base',
        'account',
        'payment',
    ],
    'data': [
        'views/account_register_payment.xml',
    ],
    'installable': True,
    'auto_install': False,
}
