# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Appraisal Performance',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Appraisal Performance',
    'description': """
    - Appraisal Performance Request
    - Approvals
    - Finance Calculation
    - Email Notification
""",
    'depends': [
        'base', 'hr', 'service_configuration_panel',
        'hr_employee_approval_tab', 'hr_contract_grade_level'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/performance_appraisal_sequence_view.xml',
        'views/performance_appraisal_view.xml',
        'views/performance_appraisal_configuration_view.xml',
        'views/rating_scale_view.xml',
        'views/performance_appraisal_value_view.xml',
        'views/personal_competency_view.xml',
        'views/objectives_view.xml',
        'views/hr_employee_view.xml',
        'wizard/performance_appraisal_wizard_view.xml',
        'wizard/objectives_locked_wizard.xml',
        'views/templates.xml',
        'views/performance_appraisal_menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
