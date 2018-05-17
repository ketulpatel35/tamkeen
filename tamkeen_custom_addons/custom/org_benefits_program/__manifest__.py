# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Benefits Program',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Benefits Program',
    'description': """
    - Benefits Program Request
    - Approvals
    - Finance Calculation
    - Email Notification
""",
    'depends': [
        'base', 'hr', 'account', 'hr_payroll','hr_contract',
        'service_configuration_panel', 'hr_employee_approval_tab',
        'hr_contract_grade_level', 'org_employee_family', 'hr_contract_init'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/grade_level_view.xml',
        'views/org_benefits_program_sequence.xml',
        'views/org_benefits_program_view.xml',
        'views/org_benefits_program_configuration_views.xml',
        'views/hr_employee_view.xml',
        'views/templates.xml',
        'views/hr_contract_view.xml',
        'wizard/org_benefits_program_remove_wiz_view.xml',
        'views/org_benefits_program_menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
