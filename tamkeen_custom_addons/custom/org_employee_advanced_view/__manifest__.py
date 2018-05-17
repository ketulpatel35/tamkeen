# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Advance View',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Advance View',
    'description': """
    - Employee Advance View
""",
    'depends': [
        'base', 'hr','org_time_recording_payroll',],
    'data': [
        'views/calendar_views.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
