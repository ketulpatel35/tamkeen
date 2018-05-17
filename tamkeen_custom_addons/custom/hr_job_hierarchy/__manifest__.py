# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Job Hierarchy',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Define Hierarchy of Jobs
========================

    1. Define parent/child relationship for jobs, which is useful for
       determining supervisor/subordinate relationships.
    2. Provide a knob in Job configuration to specify if the person with that
       job should be considered the Department manager.
    3. Automatically set the manager of a department based on this knob in
    job configuration.
    4. Automatically set an employee's manager from the department's manager.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr',
        'hr_recruitment',
        'hr_contract',
    ],
    'init_xml': [
    ],
    'data': [
        'hr_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
