# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Certificate of Completion',
    'version': '0.1',
    'category': 'Account',
    'description': """
    Certificate of Completion
""",
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'base', 'purchase', 'analytic', 'purchase_config', 'account_segments',
        'service_configuration_panel', 'purchase_order_report', 'stock',
    ],
    'data': [
        'security/ir_group.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/purchase_order_view.xml',
        'views/coc_sequence.xml',
        'views/certificate_of_completion_view.xml',
        'views/account_invoice_view.xml',
        'views/res_company_view.xml',
        'views/service_panel_configuration_view.xml',
        'views/templates.xml',
        'views/service_proof_documents_view.xml',
        'report/purchase_payment_report.xml',
        'wizard/coc_forward_to_view.xml',
        'views/menu_items_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
