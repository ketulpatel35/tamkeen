# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Recruitment Stages',
    'version': '1.0',
    'category': 'HR',
    'description': """
This module used to delete odoo standard stages and create new ones.
        """,
    'author': 'Bista Solutions',
    'website': 'https://www.open-inside.com',
    'depends': [
        'hr',
        'hr_recruitment',
    ],
    'data': [
        'stages_data.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
