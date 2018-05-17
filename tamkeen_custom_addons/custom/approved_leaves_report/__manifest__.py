# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Approved Leaves Report",
    "version": "1.0",
    "description": "Reports for Employee Approved Leaves.",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['base', 'hr', 'hr_holidays',
                'hr_employee_customization', 'hr_holidays_extension'],
    "category": "Qweb Report",
    "data": [
        'report_register.xml',
        'report/approved_leaves_report.xml',
    ],
    "installable": True,
}
