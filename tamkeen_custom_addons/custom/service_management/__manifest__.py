# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Services Management',
    'version': '1.0',
    'author': 'BistaSolutions',
    'sequence': 7,
    'category': 'Services/ESS',
    'website': 'http://www.bistasolutions.com/',
    'summary': 'Services Management and Tracking',
    'description': """
- Multi approval mechanism.
- Support many services types.
- Flexibility in creating new services types and
configuring it based on the business needs.
- Send notifications based on the workflow.
- We can set the aprovals cycle per employee.
""",
    'depends': [
        'hr',
        'document',
        'base_action_rule',
        # 'web_m2x_options',
        'hr_employee_approval_tab',
        'company_group_email',
        'hr_employee_marked_roles',
        'erp_domain_name'
    ],
    'data': [
        'security/service_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/refuse_service_reason_view.xml',
        'wizard/service_remove_wizard_view.xml',
        'views/service_view.xml',
        'views/res_company_view.xml',
        'views/hr_view.xml',
        'views/ess_service_view.xml',
        'views/service_config_view.xml',
        'views/service_menu.xml',
        'views/service_sequence.xml',
        'views/reminder_cron.xml',
        'views/templates.xml',
        # 'service_menu.xml',

    ],
    'images': [],
    'update_xml': [],
    'demo': [],
    'installable': True,
    'application': True,
}
