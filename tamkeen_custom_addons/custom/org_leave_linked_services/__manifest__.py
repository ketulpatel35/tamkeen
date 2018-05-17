# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Leave Linked Services",
    'summary': 'Organization Leave Linked Services',
    'description': """
Organization Leave Linked Services
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'service_management',
        'hr_holidays_extension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_holidays_view.xml',
        'views/service_category_view.xml'
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
