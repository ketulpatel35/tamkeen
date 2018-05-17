# -*- encoding: utf-8 -*-
{
    'name': 'Export with Timezone',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Tamkeen Team',
    'website': '',
    'category': 'web',
    'description': """
- Export date time with different time zone
""",
    'depends': ['web'],
    'data': [
        'view/load_js.xml',
    ],
    'auto_install': False,
    'qweb': [
        'static/src/xml/track_export_view.xml',
    ]
}
