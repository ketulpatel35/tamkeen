# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Organization Timesheet ESS",
    "version": "1.0",
    "description": "Organization Timesheet",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['org_timesheet_extension', 'hr_timesheet_sheet',
                'hr_dashboard'],
    "category": "hr",
    "data": [
        'views/timesheet_view.xml',
        'views/timesheet_menu.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
