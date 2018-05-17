# -*- coding: utf-8 -*-
{
    'name': 'CRM Proposal Product',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'Proposal Management',
    'sequence':  1,
    'description': """
CRM: Link Product to proposal lines
====================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'crm_proposal', 'sales_team', 'product'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'views/proposal_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
