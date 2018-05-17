# -*- coding: utf-8 -*-
{
    'name': 'CRM Activity',
    'version': '0.1',
    'author': 'Tamkeen Technolgies',
    'summary':  'Extending CRM Activity',
    'sequence':  1,
    'description': """
Extending CRM
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'sales_team', 'crm_base'],
    'data': [
        'data/sequence.xml',

        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',

        'views/crm_activity_view.xml',
        'views/crm_action_view.xml',
        'views/lead_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
