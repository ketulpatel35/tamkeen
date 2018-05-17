# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


{
    'name': 'Export Payslip to Bank IR8A File',
    'version': '0.1',
    'category': 'General Reporting',
    'website': 'http://www.bistasolutions.com/',
    'description': """
Export employees payslip details to a formatted bank IR8A text file.
""",
    'author': 'Bista Solutions',
    'depends': [
        'hr_payroll_period',
        'base',
        'hr_payroll_customization',
    ],
    'data': [
        # 'report.xml',
        # 'security/ir.model.access.csv',
        'res_company_view.xml',
        'wizard/bank_ir8a_waizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
