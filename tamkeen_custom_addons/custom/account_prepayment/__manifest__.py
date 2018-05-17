# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'PrePayment',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account & Finance',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Prepayment',
    'description': """

   This module is used to manage prepaid expenses or revenues for invoices and bills.

""",
    'depends': [
        'account'
    ],
    'data': [
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'security/account_prepayment_security.xml',
        'security/ir.model.access.csv',
        'views/account_prepayment_view.xml',
        'views/account_invoice_view.xml',
        'wizard/generate_prepaid_move_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
