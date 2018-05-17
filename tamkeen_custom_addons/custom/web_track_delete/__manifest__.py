# -*- encoding: utf-8 -*-
{
    'name': 'Web Track Delete',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Technologies',
    'website': '',
    'category': 'Web',
    'description': """
- Enable the admin to grant the delete option to specific users.
""",
    'depends': ['web'],
    'data': [
        'security/user_group.xml',
        'security/ir.model.access.csv',
        'view/track_delete_view.xml',
    ],
    'images': [],
    'auto_install': False,
}
