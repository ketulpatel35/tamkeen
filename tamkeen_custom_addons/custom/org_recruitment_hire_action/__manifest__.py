# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Recruitment Hire Action",
    'summary': 'Organization Recruitment Hire Action',
    'description': """
        Organization Recruitment Hire Action
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'personnel_actions',
        'hr_recruitment_stages',
        'hr_recruitment_stages_movement'
    ],
    'data': [
        'views/hr_recruitment_new_view.xml',
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
