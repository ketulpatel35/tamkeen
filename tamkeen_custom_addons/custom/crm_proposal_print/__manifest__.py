# -*- coding: utf-8 -*-
{
    'name': 'CRM Proposal Print',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'Printable Proposal (Quotation)',
    'sequence':  1,
    'description': """
CRM: Proposal Printing
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team', 'crm_proposal'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
