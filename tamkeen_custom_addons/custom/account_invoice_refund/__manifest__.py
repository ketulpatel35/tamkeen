# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Invoice Refund',
    'version': '1.0',
    'category': 'Account',
    'sequence': 10,
    'summary': 'Invoice Refund',
    'author': 'Bista Solutions',
    'description': """
    - Enable Customer Refund
    - Enable Vendor Refund
    """,
    'website': 'www.bistasolutions.com',
    'depends': ['base', 'account'],
    'data': [
            'views/account_invoice_view.xml',
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
