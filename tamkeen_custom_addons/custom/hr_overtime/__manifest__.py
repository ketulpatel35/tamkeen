# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Hr Overtime",
    "version": "1.0",
    "description": "Employee Overtime Calculation",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['base', 'hr', 'account_segments',
                'hr_payroll_period', 'emp_self_services', 'erp_domain_name',
                'hr_attendance_customization', 'hr_employee_approval_tab',
                'service_configuration_panel', 'hr_payslip_amendment',
                'org_shift_timeline',
                'web_readonly_bypass',
                ],
    "category": "hr",
    "data": [
        'security/user_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/overtime_sequence_view.xml',
        'wizard/generate_payslip_amendment_view.xml',
        'wizard/generate_sequenced_planned_activities_view.xml',
        'views/overtime_statement_req_view.xml',
        'views/overtime_pre_request_view.xml',
        'views/ess_overtime_view.xml',
        'views/overtime_config_panel_view.xml',
        'views/hr_employee_view.xml',
        'views/res_company_view.xml',
        'views/hr_payslip_amendment_view.xml',
        'report/overtime_report_view.xml',
        'report/report_register.xml',
        'report/overtime_claim_request_report.xml',
        'views/menu_items_overtime.xml',
        'views/reminder_cron.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
