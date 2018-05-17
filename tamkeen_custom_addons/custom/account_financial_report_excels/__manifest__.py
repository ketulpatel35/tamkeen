# -*- coding: utf-8 -*-
{
    'name': 'Financial Excel Reporting ',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Excel Report Profit & Loss / Balance Sheet...',
    'description': """You can install xlwt library in following links
     https://pypi.python.org/pypi/xlwt
        Tags:
        Account Financial Reports
        Account Financial Excel
        excel reports
        Profit and Loss Report Excel
        accounting reports
        account finance report
        Financial report
        account financial report in excel
        report in excel
        odoo community report
        odoo community accounting reports
        community accounting reports
        financial reports community

""",
    'author': 'Bista Solutions',
    'website': 'www.bistasolutions.com',
    'depends': ['account'],
    'data': [
            'security/ir.model.access.csv',
            'data/profit_loss_net_balance.xml',
            'wizard/account_financial_report_view.xml',
            'wizard/trial_balance_report_wiz.xml',
            'wizard/account_report_general_ledger_view.xml',
            'wizard/account_report_partner_ledger_view.xml',
            'wizard/ledger_view_customized.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
