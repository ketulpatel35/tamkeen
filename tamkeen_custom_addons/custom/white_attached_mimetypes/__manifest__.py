# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'White Attached Mimetype',
    'version': '1.1',
    'summary': 'White Attached Mimetype',
    'sequence': 30,
    'description': """
    White Attached Mimetype
""",
    'author': 'Bista Solutions',
    'website': '',
    'images': [],
    'depends': ['base', 'document'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/white_mimetype_view.xml',
        'views/white_mimetype_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
