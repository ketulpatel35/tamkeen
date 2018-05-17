# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Accounting Payment Workflow Customization',
    'version': '1.1',
    'author': 'Bista Solutions',
    'category': 'Accounting & Finance',
    'description': """
Overriding default odoo account workflows behaviour.
----------------------------------------------------
- Give the authority only to the accountant manager to
  post the manual journal entries.
- Change the suplliers and customers payments behaviour.
- Change assets closing behaviour.

    """,
    'depends': ['base', 'account_accountant'],
    'data': [
        'security/voucher_security.xml',
        'views/voucher_payment_receipt_view.xml',
        # 'account_voucher_workflow.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
