# -*- encoding: utf-8 -*-
{
    'name': 'Project Payments Milestone',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'project',
    'description': """
- Project Payments Milestone
""",
    'depends': ['project_management',
                'project_issue', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/sequences.xml',
        'views/project_conf_view.xml',
        'views/project_milestone_view.xml',
        'views/project_views.xml',
        'views/menu_items.xml',
        'report/report_project_charter.xml',
        'report/report_project_progress.xml',
    ],
    'auto_install': False,
}
