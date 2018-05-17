# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Department Extension',
    'version': '1.0',
    'category': 'Department',
    'description': """
Order by Parent-Child Relationship and by Sequence Number
=========================================================
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_job_categories'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/hr_department_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
