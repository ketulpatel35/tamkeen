# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Resource Calendar",
    'summary': 'Organization Resource Calendar',
    'description': """
    """,
    'category': 'Resource',
    'version': '1.0',
    'depends': [
        'resource',
        'hr_public_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/resource_calendar_view.xml',
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Tamkeen Tech',
    'maintainer': 'tamkeentech.sa',
    'website': 'http://tamkeentech.sa',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
}
