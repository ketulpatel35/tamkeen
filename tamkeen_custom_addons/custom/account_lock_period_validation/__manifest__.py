# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Lock Journal Transaction',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Account & Finance',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Lock Journal Entry',
    'description': """


""",
    'depends': [
        'account'
    ],
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'data/account_lock_period_validation_data.xml',
        'views/account_configuration_view.xml'
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
