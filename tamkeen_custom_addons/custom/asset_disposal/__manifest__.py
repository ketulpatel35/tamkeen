# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Asset Disposal',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account & Finance',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Asset Disposal',
    'description': """

   This module will allow to dispose assets.

""",
    'depends': [
        'account',
        'account_asset'
    ],
    'data': [
        'views/account_asset_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
