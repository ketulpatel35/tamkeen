# -*- coding: utf-8 -*-
{
    'name': 'CRM Proposal',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'Proposal Management',
    'sequence':  3,
    'description': """
CRM: Proposal Management
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team',],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'data/sequence.xml',

        'views/proposal_view.xml',
        'views/lead_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
