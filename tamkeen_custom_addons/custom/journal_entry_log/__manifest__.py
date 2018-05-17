# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Log Journal Entry',
    'version': '1.0',
    'category': 'Finance',
    'depends': [
        'account',
        'account_lock_period_validation'
    ],
    'author': 'Bista Solutions',
    'description': """
This module will allow to log modifications made in journal entry.
=========================================================
    """,
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'wizard/review_journal_log_view.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
