# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Purchase Order Status Report",
    "version": "1.0",
    "description": "Excel report of Purchase orders",
    "author": "Bista Solutions",
    'website': 'http://www.bistasolutions.com',
    "depends": ["base", "purchase"],
    "category": "Qweb Report",
    "data": [
        'views/purchase_order_view.xml',
    ],
    "installable": True,
}
