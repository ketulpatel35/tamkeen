# -*- encoding: utf-8 -*-

{
    'name': 'Web Track Export',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'Web',
    'description': """
- Enable the admin to grant the export option to specific users.
- Create a log for the users who exported the data from the system and keep a
log to the exported data for securing the export process.
""",
    'depends': ['base', 'web', 'survey'],
    'data': [
        'security/export_group.xml',
        'view/track_export_view.xml',
        'view/web_track_export_view.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
}
