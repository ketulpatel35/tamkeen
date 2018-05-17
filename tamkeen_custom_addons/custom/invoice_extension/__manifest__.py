# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Invoice Extension',
    'version': '1.0',
    'author': 'Bista Solutions',
    'category': '',
    'description': """
This addon to:
#############################
- Open the related purchase order for the selected invoice.
    """,
    'depends': [
        'account',
        'purchase',
        'purchase_config',
        'purchase_requisition_config',
        'erp_domain_name'
    ],
    'data': [
        'views/templates.xml',
        'views/invoice_double_validation_view.xml'
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
}
