# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'General Services Management',
    'version': '0.1',
    'author': 'Bista Solutions',
    'sequence': 1,
    'category': 'Request Management',
    'website': 'http://www.bistasolutions.com',
    'summary': 'General Services Management and Tracking',
    'description': """
- Multi approval mechanism.
- Support many services types.
- Send notifications based on the workflow.
""",
    'depends': [
        'hr',
        # 'web_m2x_options',
        'document',
    ],
    'data': [
        'security/request_security.xml',
        'security/ir.model.access.csv',
        'views/request_view.xml',
        'views/request_types_view.xml',
        'views/request_sequence.xml',
        'views/request_data.xml',
        'views/request_menu.xml',
    ],
    'installable': True,
    'application': True,
}
