# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Management",
    'summary': 'Organization Management',
    'description': """
Organization Structure
==========================
An organizational Management defines how activities such as coordination
supervision and task allocation are directed toward the achievement of
organizational aims.
    """,
    'category': 'HR',
    'version': '1.0',
    'depends': [
        'base',
        'hr',
        'hr_recruitment',
        'hr_recruitment_survey',
        'account_budget',
        # 'hr_payroll_period',
        'resource',
    ],
    # Views templates, pages, menus, options and snippets
    'data': [
        'security/ir_groups_view.xml',
        'security/ir.model.access.csv',
        'views/hr_job_template_view.xml',
        'views/hr_position_view.xml',
        'views/hr_employee_view.xml',
        'views/organization_unit_view.xml',
        'views/hr_employee_group_view.xml',
        'views/personnel_area_view.xml',
        'views/organization_sequence_view.xml',
        'views/menu_view.xml',
    ],
    # Qweb templates
    'qweb': [],
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
