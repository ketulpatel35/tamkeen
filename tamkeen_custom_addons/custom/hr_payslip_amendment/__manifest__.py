# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Pay Slip Amendment',
    'version': '1.0',
    'category': 'Generic Modules/Company Data',
    'author': 'Bista Solutions',
    'description': """
Add Amendments to Current and Future Pay Slips
==============================================
    """,
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr_payroll_customization',
        'hr_employee_id',
        'web_readonly_bypass',
        # 'hr_payroll_period'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/hr_payslip_amendment_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
