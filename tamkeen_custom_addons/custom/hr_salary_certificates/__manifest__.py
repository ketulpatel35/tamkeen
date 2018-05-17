# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employment Certificate',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': 'Employment Certificate',
    'description': """

   This module allow HR department to manage Employment Certificate.
   Hr Employment Certificate Approval functionality
   Employment Certificate notification employee Inbox

""",
    'depends': [
        'base', 'hr', 'hr_payroll', 'hr_payroll_ess',
        'hr_payslip_amendment', 'report', 'hr_payroll_salary_rules',
        'hr_saudi_filed'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/emp_salary_certificates_view.xml',
        'views/destination_organization_view.xml',
        'views/purpose_view.xml',
        'views/salary_rule_to_be_display_view.xml',
        'wizard/certificates_reject_reason_view.xml',
        'wizard/generate_payslip_amendment_view.xml',
        'report/salary_certificates_report_template.xml',
        'report/salary_certificate_report_arabic.xml',
        'report/report_register.xml',
        'views/res_bank_view.xml',
        'views/res_company_view.xml',
        'wizard/salary_certificates_report_wizard_view.xml',
        'views/templates.xml',
        'views/menu_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
