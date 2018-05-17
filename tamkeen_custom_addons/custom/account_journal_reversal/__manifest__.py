# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Journal Reversal',
    'version': '9.0.1.0.0',
    'category': 'Accounting',
    'author': 'Bista solutions,',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'account','invoice_extension','finance_authority_matrix',
    ],
    'data': [
        'security/groups.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
