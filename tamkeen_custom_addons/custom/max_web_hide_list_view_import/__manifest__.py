# -*- coding: utf-8 -*-
{
    'name': "Web Hide List View Import Button",

    'summary': """
        To hide import button of list view for non-admin user.
    """,

    'description': """
        To hide import button of list view for non-admin user.
    """,

    'author': "MAXodoo",
    'website': "http://www.maxodoo.com",
    'category': 'web',
    'version': '10.0.0.1',
    'depends': ['base', 'base_import'],
    'data': [
        'security/groups_view.xml',
        'security/ir.model.access.csv',
        'views/max_web_hide_list_view_import_view.xml',
    ],
}
