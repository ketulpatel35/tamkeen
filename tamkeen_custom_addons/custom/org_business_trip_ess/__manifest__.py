# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Business Trip ESS',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Business Trip ESS',
    'description': """
    - Business Trip Request
    - Employee Self Service
""",
    'depends': ['org_business_trip'],
    'data': [
        'views/org_business_trip_view.xml',
        'views/org_business_trip_menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
