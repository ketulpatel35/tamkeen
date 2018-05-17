# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Analytic Parent',
    'summary': """
        This module reintroduces the hierarchy to the analytic accounts.""",
    'version': '10.1',
    'author': 'Bista Solutions',
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'account_accountant',
        'analytic',
    ],
    'data': [
        'views/account_analytic_account_view.xml',
        'wizard/account_analytic_chart_view.xml',
        # 'report/cost_center_report_view.xml'
    ]
}
