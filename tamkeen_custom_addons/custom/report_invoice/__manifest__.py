# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    "name": "Invoice Reports",
    "version": "1.2",
    "description": "Reports for customer & supplier invoices module",
    "author": "Bista Solutions",
    'website': 'http://www.bistasolutions.com',
    "depends": ["base", "account"],
    "category": "Generic Modules/QWeb Report",
    'data': ["report_invoice.xml",
             "report_invoice_template.xml",
             ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
