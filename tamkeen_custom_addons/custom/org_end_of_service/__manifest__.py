# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'End of Service',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'End of Service',
    'description': """
    - End of Service Request
    - Approvals
    - Manage Meetings and Negotiate
    - Finance Calculation
    - End of Service Benefits Calculation as per Saudi Labor Law.
    - Email Notification
""",
    'depends': [
        'base', 'hr', 'calendar', 'organization_structure',
        'service_configuration_panel', 'hr_employee_approval_tab'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/recommend_negotiation_wizard_view.xml',
        'views/org_end_of_service_sequence.xml',
        'views/org_end_of_service_views.xml',
        'views/org_end_of_service_type_views.xml',
        'views/org_end_of_service_configuration_views.xml',
        'views/hr_employee_view.xml',
        'views/calendar_views.xml',
        'views/templates.xml',
        'views/org_end_of_service_menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
