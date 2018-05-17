# -*- coding: utf-8 -*-
{
    'name': 'CRM Proposal Shipping',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'Proposal shipping Info.',
    'sequence':  1,
    'description': """
CRM: Adding Proposal Shipping Information
===============================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team', 'crm_proposal'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        
        'views/shipping_method_view.xml',
        'views/proposal_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
