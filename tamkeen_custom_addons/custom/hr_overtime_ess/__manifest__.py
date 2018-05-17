# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Hr Overtime ESS",
    "version": "1.0",
    "description": "Employee Overtime Calculation",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['hr_overtime', 'web_readonly_bypass', 'hr_dashboard'],
    "category": "hr",
    "data": [
        # 'views/overtime_view.xml',
        'views/overtime_menu.xml',
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
