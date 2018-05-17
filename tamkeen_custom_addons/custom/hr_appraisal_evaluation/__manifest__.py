# -*- coding: utf-8 -*-
{
    'name': "Employee Appraisal",

    'summary': """
        Employee Can Apply for the Appraisal for the Dedicated Period,
        Manager Will rate the Employee,
        HR will review and give the Average Rate,
        CEO will finalized it""",

    'description': """
        -> Employee will fill up the Appraisal
         from with necessary details in it,
        -> Then the Appresal Form will be sent
         to Manager which the Employee has selected in the Form,
        -> Manager will Review the Appraisal Form
         of the Employees and fill it up with Details in it,
        -> Then the Manager will sent that Forms
         to HR where HR will do the Review ,
        -> HR will fill up the detials Left and give rating,
        -> HR will sent that form to CEO for Approval Process,
    """,

    'author': "Bista Solutions",
    'website': "http://www.bistasolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/
    # blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'hr_employee_customization',
                'hr_admin',
                ],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'data/mail_template_emp_appraisal.xml',
        'security/ir.model.access.csv',
        'views/objective.xml',
        'wizard/hr_get_employee_wizard.xml',
        'wizard/employee_obj_cancell_wiz.xml',
        'views/emp_appraisal_year_view.xml',
        'views/appraisal_email_templates.xml',
        'views/emp_appraisal_serial_no.xml',
        'views/employee_appraisal.xml',
        'views/behaviour_competences.xml',
        'views/individual_development_plan.xml',
        'views/career_discussion.xml',
        'views/Requirement_category.xml',
        'views/rating_master.xml',
        'reports/employee_appraisal_report_template.xml',
        'views/hr_appraisal_menu.xml',
        'views/emp_objective_res_config.xml',
        'views/emp_objective_performance_mgmt.xml',

    ],
    'installable': True,
    'auto_install': False
}
