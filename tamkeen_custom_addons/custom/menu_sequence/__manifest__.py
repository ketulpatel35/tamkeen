# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Menu Sequence',
    'version': '1.0',
    'category': 'Menu',
    'description': """
    Menu Sequence
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_holidays',
        'hr_contract',
    ],
    'data': [
        'views/menu_sequence_manage.xml'
    ],
    'installable': True,
}
