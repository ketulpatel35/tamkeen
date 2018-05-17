# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Level Indexing",
    'summary': 'Organization Structure',
    'description': """
        Organization Level Indexing
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'organization_structure',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/level_indexing_view.xml',
        'views/menu_view.xml',
        'views/level_indexing_relation_view.xml'
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Bistasolutions.com',
    'maintainer': 'bistasolutions.com',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    # Technical options
    'demo': [],
    'test': [],
    'installable': True,
    # 'auto_install':False,
    # 'active':True,
}
