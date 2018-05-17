# -*- coding: utf-8 -*-
{
    'name': 'CRM Service Stages',
    'version': '0.1',
    'author': 'Tamkeen Technologies',
    'summary':  'CRM Workflow',
    'sequence':  3,
    'description': """
CRM Workflow
=================================
    """,
    'website': 'http://www.tamkeentech.sa',
    'depends': [
        'base',
        'crm',
        'crm_base',
        'crm_qualification',
        'crm_proposal',
        'crm_activity',
    ],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'data/activity_data.xml',
        'data/stage_data.xml',

        'views/stage_control_view.xml',
        'views/stage_view.xml',
        'views/lead_view.xml',
        'views/team_view.xml',
        'views/actions_and_menus.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
