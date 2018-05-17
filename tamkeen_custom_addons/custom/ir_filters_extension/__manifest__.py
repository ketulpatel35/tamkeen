# -*- coding: utf-8 -*-
##############################################################################

{
    'name': 'System Filters Security',
    'version': '0.1',
    'category': 'Access Rights',
    'description': """
System Filters Security
""",
    'author': 'Tamkeen ERP Team',
    'depends': [
        'base',
        'hr_admin',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
