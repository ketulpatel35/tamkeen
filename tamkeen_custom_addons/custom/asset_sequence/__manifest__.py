# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Asset Sequence',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'website': 'http://www.bistasolutions.com/',
    'category': 'account',
    'description': """
This Module add barcode sequence, type fields to Asset
Add Asset Type configuration menu

    """,
    'depends': [
        'base',
        'account_asset',
        'hr',
        'account'
    ],
    'data': [
        'view/sequence.xml',
        'view/asset_view.xml',
        'view/asset_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
    'application': True
}
