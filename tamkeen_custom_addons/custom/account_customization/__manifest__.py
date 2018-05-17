# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Customization',
    'version': '0.1',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'description': """
    1) This module add Arabic Fields for chart of account
    2) the reference number with next number automatically
    3) Overriding default odoo account module:
    * Only to the accountant manager to post the manual journal entries.
    * Give permission for Finance manager on purchase order line
    """,
    'depends': [
        'base',
        'account',
        'payment',
        'account_cancel',
        'analytic',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/account_voucher_sequence.xml',
        'views/res_partner_view.xml',
        'views/account_view.xml',
        'views/account_voucher_view.xml',
        # 'wizard/ledger_view_customized.xml',
    ],
    'installable': True,
    'auto_install': False,
}
