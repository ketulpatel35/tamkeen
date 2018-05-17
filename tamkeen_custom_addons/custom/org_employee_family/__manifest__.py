# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Employee Profile",
    'summary': 'Employment Profile',
    'description': """
Contract
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'hr',
        'hr_employee_customization',
        'emp_self_services'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/employee_family_info_view.xml',
        'views/employee_view.xml',
        'views/menu_view.xml'
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
