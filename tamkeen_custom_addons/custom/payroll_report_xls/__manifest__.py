# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Report in Excel Format',
    'version': '1.1',
    'category': 'payroll',
    'depends': [
        # 'hr_payroll_period',
        'hr_payslip_addtion',
        'erp_domain_name'
    ],
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'description': """
Payroll Report in Excel Format
=======================================

U1014
""",
    'data': [
        'wizard/payroll_excel_view.xml',
    ],

    'installable': True,
    'auto_install': False
}
