# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Analytic Customization',
    'summary': """
        This module reintroduces the hierarchy to the analytic accounts.""",
    'version': '10.1',
    'author': 'Bista Solutions',
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'account_accountant',
        'analytic',
        'account_budget',
        'hr_timesheet',
        'sale'
    ],
    'data': [
        'views/account_analytic_account_view.xml',
        'views/account_analytic_analysis_cron.xml',
    ]
}
