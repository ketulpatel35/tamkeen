# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'KSA VAT Invoice Line Report',
    'version': '1.0',
    'category': 'Finance',
    'depends': [
        'date_range',
        'ksa_vat',
    ],
    'author': 'Bista Solutions',
    'description': """
This module will allow to generate report for invoice lines in which tax is added.
=========================================================
    """,
    'data': [
        'security/ksa_vat_report_security.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'wizard/tax_report_wiz_view.xml'
    ],
    'installable': True,
    'auto_install': False
}
