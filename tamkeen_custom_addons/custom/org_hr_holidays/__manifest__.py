# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization HR Holidays",
    'summary': 'Organization HR Holidays',
    'description': """
Organization HR Holidays
    """,
    'category': 'HRMS',
    'version': '1.0',
    'depends': [
        'organization_structure',
        'hr_holidays_extension',
        'org_structure_payroll',
        'hr_contract_grade_level',
    ],
    'data': [
        'views/hr_holidays_view.xml'
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
