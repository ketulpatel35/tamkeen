# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Structure Analytic Account",
    'summary': 'Organization Structure Analytic Account',
    'description': """
Organization Structure
==========================
    """,
    'category': 'Account',
    'version': '1.0',
    'depends': [
        'analytic',
        'organization_structure'
    ],
    'data': [
        'views/analytic_account_view.xml',
        'views/hr_department_view.xml',
        'views/menu_view.xml',
        'views/hr_job_view.xml'
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
