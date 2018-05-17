# -*- coding: utf-8 -*-
{
    'name': 'CRM Customer Account',
    'version': '0.1',
    'author': 'Tamkeen',
    'summary':  'Customers Directory',
    'suequence':  1,
    'description': """
CRM: Customer Directory
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team', 'base_partner_prospect', 'crm_partner_prospect'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'views/partner_view.xml',
        'views/lead_view.xml',
        'views/actions_and_menus.xml',

        'email_templates/forward_to_account_manager.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
