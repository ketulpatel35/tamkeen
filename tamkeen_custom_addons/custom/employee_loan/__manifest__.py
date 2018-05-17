# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee Loan Management',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Loan Management',
    'description': """

   This module allow HR department to manage loan of employees.
   Hr Loan Approval functionality
   Loan notification employee Inbox

""",
    'depends': [
        'service_configuration_panel',
        'hr_payroll',
        'account_segments',
        'hr_attendance_customization',
        'hr_employee_approval_tab',
        'hr_payslip_amendment',
        'hr_payroll_period',
        'web_readonly_bypass'
    ],
    'data': [
        'views/loan_sequence.xml',
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/generate_payslip_amendment_view.xml',
        'wizard/employee_loan_remove_wizard_view.xml',
        'wizard/reschedule_issuing_date_view.xml',
        'views/employee_loan_view.xml',
        'views/templates.xml',
        'views/loan_configuration.xml',
        'views/hr_employee_view.xml',
        'report/loan_clearance_report_view.xml',
        'report/loan_request_report.xml',
        'report/loan_report_xls_view.xml',
        'report/report_register.xml',
        'views/loan_action_view.xml',
        'views/hr_payslip_amendment_view.xml',
        'views/loan_menu_view.xml',
        'views/reminder_cron.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
