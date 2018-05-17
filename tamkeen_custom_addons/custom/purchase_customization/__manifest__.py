# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Purchase Customization',
    'version': '1.1',
    'category': 'Purchase Customization',
    'depends': ['purchase_requisition', 'account', 'purchase',
                'purchase_config', 'purchase_requisition_config'],
    'author': 'Bista solutions',
    'website': 'http://www.bistasolutions.com',
    'description': """
    Override all purchase view fields
     to be readonly except in the draft and sent states.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_view.xml',
        'views/purchase_config.xml',
        'views/account_view.xml',
        'report/purchase_requisition_template.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'auto_install': False
}
