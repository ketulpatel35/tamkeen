# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Hr holidays Extension',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_public_holidays',
        'hr_admin',
        'hr_holidays',
        'calendar',
        'erp_domain_name',
        'hr_employee_approval_tab',
        'web_readonly_bypass',
        'org_shift_timeline',
        'hr_employee_id',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/templates.xml',
        'wizard/refuse_leave_reason_view.xml',
        'wizard/employee_leave_remove_wizard_view.xml',
        'views/hr_holidays_view.xml',
        'views/leave_proof_view.xml',
        'views/leave_menu_view.xml',
        'views/res_company_view.xml',
        'views/hr_employee_view.xml',
        'views/employee_leave_summary_view.xml'

    ],
    'installable': True,
    'auto_install': False,
}
