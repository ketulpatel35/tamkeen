# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Appraisal Performance ESS',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Self Service Appraisal Performance',
    'description': """
    - Appraisal Performance Employee Self Service
""",
    'depends': [
        'org_performance_appraisal', 'emp_self_services'
    ],
    'data': [
        'views/performance_appraisal_view.xml',
        'views/performance_appraisal_menu_view.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
