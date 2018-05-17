# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Configuration',
    'version': '1.1',
    'category': 'Purchase Management',
    'depends': ['purchase', 'base_action_rule', 'stock',
                'hr_admin', 'account', 'erp_domain_name'
                ],
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'description': """
This module is for the specification of Tamkeen technologies purchase.
=========================================================
This module modifies the purchase work-flow in order to validate purchases
by Budget manager.
It also send a mail notification in creation of new product.This mail is
automatically sent to the financial manager.
* the payment terms in the PO is mandatory after the installation
    """,
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/purchase_order_sequence.xml',
        'views/purchase_view.xml',
        'views/product.xml',
    ],

    'installable': True,
    'auto_install': False
}
