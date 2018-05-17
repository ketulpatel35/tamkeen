# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'ESS Services Management',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 7,
    'category': 'Services/ESS',
    'website': '',
    'summary': 'Services requests and approvals',
    'description': """
- Enable the service management to be displayed in ESS.
""",
    'depends': [
        'service_management',
        'emp_self_services',
        'hr_dashboard' # only for the MSS and ESS menu items and Dashbord.
    ],
    'data': [
        'views/service_menu.xml',
        'views/hr_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'images': [],
    'update_xml': [],
    'demo': [],
    'installable': True,
    'application': True,
}
