# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Analytic Journal',
    'summary': """
        This module add analytic accounts journals.""",
    'version': '10.1',
    'author': 'Bista Solutions',
    'category': 'Account',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'finance_authority_matrix',
        'account_accountant',
        'analytic',
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_analytic_journal_view.xml',
        'report/report_analytic_journal_template.xml',
        'wizard/account_analytic_journal_report_view.xml',
    ]
}
