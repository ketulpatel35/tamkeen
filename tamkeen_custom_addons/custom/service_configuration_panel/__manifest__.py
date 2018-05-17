# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Service Configuration Panel",
    "version": "1.0",
    "author": "Tamkeen Technologies",
    "category": 'Generic Approval',
    "description": """
    """,
    'website': 'http://tamkeentech.sa/',
    "depends": ['base', 'hr_employee_marked_roles'],
    'data': [
        'security/user_groups.xml',
        'views/service_config_view.xml',
        'views/service_menu.xml',
        'views/res_company_view.xml',
        'views/service_proof_documents_view.xml',
        'wizard/service_panel_wizard_view.xml',
        'wizard/service_log_wizard_view.xml',
    ],
    'installable': True,
    'active': False,
}
