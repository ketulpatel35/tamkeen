# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Leave Linked Amendment',
    'version': '1.0',
    'category': 'Leave',
    'author': 'Bista Solutions',
    'description': """
Add Leave Amendments to Current and Future Pay Slips
==============================================
    """,
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr_holidays',
        'hr_holidays_extension',
        'hr_payslip_amendment',
        'org_holidays_by_hours',
    ],
    'data': [
        'wizard/leave_linked_amendment_view.xml',
        'views/hr_holidays_status_view.xml',
        'views/hr_holidays_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
