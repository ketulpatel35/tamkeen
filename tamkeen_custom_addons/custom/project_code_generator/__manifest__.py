# -*- encoding: utf-8 -*-
{
    'name': 'Project Code Generator',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'Project',
    'description': """
- Project Code Generator
""",
    'depends': ['project_management',],
    'data': [
        'security/ir.model.access.csv',
        'views/project_view.xml',
        'wizard/generate_code.xml',
        'report/project_progress_report.xml',
    ],
    'auto_install': False,
}
