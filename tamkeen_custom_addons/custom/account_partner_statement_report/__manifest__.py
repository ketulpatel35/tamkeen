# -*- coding: utf-8 -*-
{
    'name': 'Account Partner Statements',
    'version': '10.0.1.0.1',
    'category': 'Reporting',
    'summary': 'Partner Statements Report',
    'author': 'Bista Solutions Inc.',
    "website": "https://www.bistasolutions.com/",
    'depends': [
        'account',
        'account_fiscal_year',
        'report_xlsx',
        'report',
    ],
    'data': [
        'wizard/partner_statement_report_wizard_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
