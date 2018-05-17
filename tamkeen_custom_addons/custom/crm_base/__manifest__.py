# -*- coding: utf-8 -*-
{
    'name': 'Base CRM',
    'version': '0.1',
    'author': 'Tamkeen Technolgies',
    'summary':  'Extending CRM',
    'sequence':  1,
    'description': """
Extending CRM
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'sales_team'],
    'data': [
        'data/sequence.xml',

        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',

        'views/lead_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
