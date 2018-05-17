# -*- encoding: utf-8 -*-
{
    'name': 'Project Management Advance View',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'project',
    'description': """
- Project Management
""",
    'depends': ['project','project_management','project_milstone_schedule',
                'project_issue'],
    'data': [
        'report/project_report_views.xml',
        'views/project_dashboard_view.xml',
    ],
    'auto_install': False,
}
