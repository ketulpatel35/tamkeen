# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': "HR Dashboard",

    'summary': """
        Dashboard For HR managers and Officers.
        """,

    'description': """
        Dashboard which includes employee details, total worked hours charts, payroll analysis,
        menus and count of approvals needed and logged in user details
    """,

    'author': "Hilar AK",
    'website': "https://www.linkedin.com/in/hilar-ak/",
    'category': "Generic Modules/Human Resources",
    'version': "10.0.1.1.0",
    'depends': [
        'base', 'hr', 'hr_expense', 'hr_attendance', 'hr_holidays',
        'hr_payroll', 'hr_recruitment', 'website_hr', 'hr_timesheet_sheet',
        'emp_self_services'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_dashboard.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'images': ["static/description/banner.gif"],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
