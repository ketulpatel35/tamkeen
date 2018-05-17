# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Vendor Bill Batch Approval',
    'version': '1.1',
    'author': 'Bista Solutions',
    'category': 'Accounting & Finance',
    'description': """
    """,
    'depends': ['base', 'invoice_extension', 'account',
                'account_batch_payment_diff', 'certificate_of_completion'],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_sequence.xml',
        'views/vendar_bill_batch_approval_view.xml',
        'wizard/vendor_bill_app_wiz_view.xml',
        'views/menu_items_view.xml',
        'views/account_payment_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
