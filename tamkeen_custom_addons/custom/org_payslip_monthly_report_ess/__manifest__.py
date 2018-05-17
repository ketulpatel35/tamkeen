# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payslip Monthly report',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Payslip Monthly report',
    'description': """

  This module allows to generate Payslip Monthly report.

""",
    'depends': [
        'hr_payroll',
        'org_hr_reports_signature',
    ],
    'data': [
        'report/report_register.xml',
        'report/report_payslip_details.xml',
        'report/payslip_report.xml',
        # 'views/payslip_report.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
