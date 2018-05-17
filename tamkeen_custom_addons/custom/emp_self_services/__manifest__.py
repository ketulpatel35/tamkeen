# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Employee/Manager Self Services',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'hr',
    'website': 'http://www.bistasolutions.com',
    'summary': ' Self Services',
    'description': """

    This module do the following:
    1. Add Documents and Sponsorship info to Employee profile
    2. Employee Information by default filter
    3. Leave requests to approve by manager menu
    4. Remove all leaves from HR in ESS tab

""",
    'depends': [
        'hr',
        'hr_contract',
        'hr_holidays',
        'hr_employee_customization',
        'web_readonly_bypass'
    ],
    'data': [
        'security/hr_security.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/hr_experiences_view.xml',
        'views/hr_qualifications_view.xml',
        'views/hr_trainings_view.xml',
        'views/hr_empl_view.xml',
        'views/hr_services_menu.xml',
        'views/templates.xml',
        'wizard/archive_unarchive_rec_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
