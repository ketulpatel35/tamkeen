# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Management/Payroll",
    'summary': 'Organization Management',
    'description': """
    """,
    'category': 'Organization Management',
    'version': '1.0',
    'depends': [
        'organization_structure',
        'hr_contract_grade_level',
        'hr_payroll'
    ],
    'data': [
        'views/hr_job_template_view.xml',
        'views/hr_position_view.xml',
        'views/menu_view.xml'
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Tamkeen Tech',
    'maintainer': 'tamkeentech.sa',
    'website': 'http://tamkeentech.sa',
    'license': 'AGPL-3',
    # Technical options
    'demo': [],
    'test': [],
    'installable': True,
    # 'auto_install':False,
    # 'active':True,
}
