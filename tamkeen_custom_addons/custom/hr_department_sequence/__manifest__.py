# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Department Sequence',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Order by Parent-Child Relationship and by Sequence Number
=========================================================
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
    ],
    'data': [
        'hr_department_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
