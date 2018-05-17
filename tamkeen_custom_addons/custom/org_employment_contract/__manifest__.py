# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Employment Contract",
    'summary': 'Employment Contract',
    'description': """
Contract
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'organization_structure',
        'hr_contract'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/employment_contract_view.xml',
        'views/menu_view.xml'
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
