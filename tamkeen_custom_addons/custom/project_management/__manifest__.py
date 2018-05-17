# -*- encoding: utf-8 -*-
{
    'name': 'Project Management',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'project',
    'description': """
- Project Management
""",
    'depends': ['base', 'project', 'hr', 'rating_project', 'purchase',
                'account_segments','hr_timesheet'],
    'data': [
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/sequences.xml',
        'security/ir_rule.xml',
        'views/project_risks_view.xml',
        'views/project_task_view.xml',
        'views/project_issue_view.xml',
        'views/project_conf_view.xml',
        'views/project_documents_view.xml',
        'views/project_views.xml',
        'views/project_stages_view.xml',
        'views/menu_items_view.xml',
        'report/report_register.xml',
        'report/report_project_charter.xml',
        'report/report_project_progress_report.xml',
        'views/res_partner_view.xml',
        'wizard/project_report.xml',
    ],
    'auto_install': False,
}
