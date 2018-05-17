# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Recruitment Stages Movements',
    'version': '1.0',
    'category': 'HR',
    'description': """
This module used to delete odoo standard stages and create new ones.
        """,
    'author': 'Bista Solutions',
    'website': 'https://www.bistasolutions.com',
    'depends': [
        'base',
        'hr',
        'hr_recruitment',
        'hr_recruitment_stages',
        'emp_self_services',
        'hr_recruitment_customization',
        'hr_admin',
        'hr_contract_grade_level',
        'hr_recruitment_survey',
        # in v8 not available but need to add for v10.
        # 'hr_applicant_document', # in v10 module mearged with hr_recruitment.
        'calendar',
        'erp_domain_name'
    ],
    'data': [
        # 'hr_recruitment_view.xml',
        'security/groups.xml',
        'views/hr_recruitment_new_view.xml',
        'views/hr_recruitment_menu.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'report/local_candidate_templete.xml',
        'report/expat_candidate_template.xml',
        'report/employment_summary_template.xml',
        'report/emp_sum_dep_manager_templete.xml',
        'views/report_register.xml',
        'views/templates.xml',
        'views/sequences.xml',
        'views/calendar_view.xml',
        # 'views/grade_level_view.xml',
        'views/calendar_template_meeting_invitation.xml',
    ],
    'installable': True,
    'auto_install': False,
}
