# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Payroll Extension',
    'category': 'Human Resources',
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'version': '1.0',
    'description': """
Extended set of Payroll Rules and Structures
============================================

    - Detailed caclculatation of worked hours, leaves, overtime, etc
    - Overtime
    - Paid and Unpaid Leaves
    - Federal Income Tax Withholding rules
    - Provident/Pension Fund contributions
    - Various Earnings and Deductions
    - Payroll Report
    """,
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'views/hr_payroll_view.xml',
    ],
    'active': True,
    'installable': True,
}
