# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Business Trip',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employee Business Trip',
    'description': """
    - Business Trip Request
    - Approvals
    - Finance Calculation
    - Email Notification
""",
    'depends': [
        'base', 'hr', 'account', 'hr_holidays', 'service_configuration_panel',
        'hr_employee_approval_tab', 'service_management',
        'hr_contract_grade_level'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/org_business_trip_view.xml',
        'views/org_business_trip_sequence.xml',
        'views/org_business_trip_configuration_views.xml',
        'views/org_business_trip_allowance_view.xml',
        'views/hr_employee_view.xml',
        'views/templates.xml',
        'views/service_category_view.xml',
        'wizard/org_business_trip_remove_wiz_view.xml',
        'views/org_business_trip_menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
