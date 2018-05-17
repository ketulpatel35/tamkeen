# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Purchase Order Report",
    "version": "1.0",
    "description": "Report for purchase order module",
    "author": "Bista Solutions",
    'website': 'http://www.bistasolutions.com',
    "depends": ["base", "purchase", "purchase_config",
                'purchase_requisition', 'account_segments',
                'erp_domain_name'],
    "category": "Qweb Report",
    "data": [
        'report/purchase_payment_report.xml',
        'report_register.xml',
        'report/po_report_menu.xml',
        'report/po_report.xml',
        'report/po_status_report.xml',
        'report/po_report_inherit.xml',
        'wizard/po_status_wizard_view.xml',
        'views/purchase_order_inherit_view.xml'
    ],
    "installable": True,
}
