# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "End of Service ESS",
    "version": "1.0",
    'summary': 'End of Service ESS',
    'description': """
    # Employee Self Service
    > Employee Request
    > Manager Approvals
    > VP Approval
    > CEO Approvals
    """,
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['emp_self_services', 'org_end_of_service'],
    "category": "hr",
    "data": [
        'views/end_of_service_view.xml',
        'views/end_of_service_menu_view.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
