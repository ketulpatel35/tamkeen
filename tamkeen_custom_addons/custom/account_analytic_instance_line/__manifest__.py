# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Analytic Instance Line',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'sequence': 1,
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'description': """
    Account Analytic Instance Line
    """,
    'depends': [
        'account',
        'purchase_requisition'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_requisition_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
