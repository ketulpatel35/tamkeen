# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Leaves Cleansing xls Report',
    'version': '1.0',
    "author": "Bista solutions",
    "website": "http://www.bistasolutions.com",
    'category': 'HR/Leave/Report',
    'description': """
                Leaves Cleansing xls Report
    """,
    'depends': [
        'base',
        'hr_holidays',
        'hr_employee_id',
        'hr_employee_customization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/leaves_cleansing_report_wiz_view.xml',
        'views/menuitems_view.xml',
        # 'views/templates.xml',
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
    'application': True
}
