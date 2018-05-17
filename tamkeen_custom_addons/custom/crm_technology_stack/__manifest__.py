# -*- coding: utf-8 -*-
{
    'name': 'CRM Technology Stack',
    'version': '0.1',
    'author': 'Tamkeen Technolgies',
    'summary':  'Extending CRM',
    'sequence':  1,
    'description': """
Adding List of (Technology Stack) to Opportunity View
======================================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',

        'views/technology_view.xml',
        'views/lead_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
