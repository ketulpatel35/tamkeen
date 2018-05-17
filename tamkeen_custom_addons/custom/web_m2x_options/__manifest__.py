# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    "name": 'web_m2x_options',
    "version": "10.0",
    "depends": [
        'base',
        'web',
    ],
    "description": """
        Web Many2one Options for all object through Configuration
        """,
    'qweb': [
        'static/src/xml/base.xml',
    ],
    'license': '',
    'data': ['views/view.xml'],
    "author": "Bista Solutions",
    'website': 'http://www.bistasolutions.com',
    'installable': True,
    'auto_install': False,
    'application': True
}
