# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'KSA VAT',
    'version': '1.0',
    'category': 'Finance',
    'depends': [
        'base',
        'account',
        'purchase_order_report',
    ],
    'author': 'Bista Solutions',
    'description': """
This module will allow to add VAT number for customers and vendors.
=========================================================
    """,
    'data': [
        'views/res_partner_view.xml',
        'views/account_invoice_view.xml',
        'report/po_report.xml',
    ],
    'installable': True,
    'auto_install': False
}
