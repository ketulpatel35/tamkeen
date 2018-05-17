# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Employee Loan ESS",
    "version": "1.0",
    "description": "Employee Loan",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['employee_loan', 'hr_dashboard'],
    "category": "hr",
    "data": [
        'views/loan_view.xml',
        'views/loan_menu.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
