# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Budget Validation',
    'version': '1.0',
    'category': 'Purchase Management',
    'depends': [
        'purchase',
        'purchase_requisition',
        'purchase_requisition_config',
        'purchase_order_report'
    ],
    'author': 'Bista Solutions',
    'description': """
This module is for the purchase Budget Validation.
=========================================================
    """,
    'data': [
        'views/purchase_requisition_view.xml',
        'views/purchase_order_inherit_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
