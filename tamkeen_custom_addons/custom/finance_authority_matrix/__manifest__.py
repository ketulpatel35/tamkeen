# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Finance Authority Matrix',
    'version': '0.1',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'description': """
    """,
    'depends': [
        'base',
        'account',
        # 'emp_self_services',
        'account_voucher',
        'product_extension',
        'account_budget',
        'account_asset',
        'account_financial_report_qweb',
        'account_financial_report_excels',
        'date_range',
        'account_invoice_refund',
        'invoice_extension',
        'res_partner_extension',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/finance_authority_matrix.xml',
        'views/account_view.xml',
        'views/asset_view.xml',
        'views/budget_view.xml',
        'views/invoice_view.xml',
        'views/payment_view.xml',
        'views/account_config_view.xml',
        'views/partner_extension_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
