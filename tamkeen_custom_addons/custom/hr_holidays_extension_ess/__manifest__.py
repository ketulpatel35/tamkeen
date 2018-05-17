# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Hr holidays Extension ESS',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_holidays_extension',
        'web_readonly_bypass',
        'emp_self_services',
        'hr_dashboard'
    ],
    'data': [
        'views/hr_holidays_ess_view.xml',
        'views/hr_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'installable': True,
    'auto_install': False,
}
