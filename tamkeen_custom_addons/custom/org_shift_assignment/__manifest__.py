# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Shift Assignment",
    'summary': 'Organization Shift Assignment',
    'description': """
    """,
    'category': 'Shift Assignment',
    'version': '1.0',
    'depends': [
        'resource',
        'org_shift_timeline', 'analytic'
    ],
    'data': [
        'wizard/shift_assignment_view.xml'
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
}
