# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Payment Report",
    "version": "1.0",
    "description": "Report for accounting Customer / Supplier payment",
    "author": "bistasolutions",
    'website': 'http://www.bistasolutions.com',
    "depends": ['base', 'account_accountant'],
    "category": "Qweb Reporting",
    'data': [
        'report_register.xml',
        'report/payment_report.xml',
    ],
    "installable": True,
    "license": "GPL-3 or any later version",
}
