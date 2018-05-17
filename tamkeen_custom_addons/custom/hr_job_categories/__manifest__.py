# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Job Categories',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Attach Categories (Tags) to Employees Based on Job Position
===========================================================

This module is useful for tagging employees based on their
job positions. For example,all Supervisors could be attached
to the Supervisors category. Define which categries a job
belongs to in the configuration for the job. When an
employee is assigned a particular job the categories attached
to that job will be attached to the employee record as well.
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr', 'hr_contract', 'hr_recruitment', 'survey'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'hr_view.xml',
    ],
    'installable': True,
    'active': False,
}
