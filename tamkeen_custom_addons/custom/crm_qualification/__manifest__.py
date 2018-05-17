# -*- coding: utf-8 -*-
{
    'name': 'CRM Qualification',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'Opportunity Qualification',
    'sequence':  1,
    'description': """
Extending CRM (Add Qualification Status)
==========================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': ['base', 'crm', 'crm_base', 'sales_team', 'survey'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'views/survey_view.xml',
        'views/lead_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
