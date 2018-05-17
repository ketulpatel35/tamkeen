# -*- coding: utf-8 -*-
{
    'name': "Employee Appraisal ess",

    'summary': """
       """,

    'description': """
        \n--> Employee Can Apply for the Appraisal for the Dedicated Period,
        \n--> Manager Will rate the Employee,
        \n--> HR will review and give the Average Rate,
        \n--> CEO will finalized it
    """,

    'author': "Tamkeen Technologies",
    'website': "",
    'version': '0.1',
    'depends': ['base',
                'hr',
                'hr_appraisal_evaluation',
                'emp_self_services',
                ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/employee_appraisal_view.xml',
        'views/employee_appraisal_menu.xml',
    ],
    'installable': True,
    'auto_install': False
}
