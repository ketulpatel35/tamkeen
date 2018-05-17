# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Attendance Employee Summary Report',
    'version': '1.0',
    'category': 'Attendance',
    'description': """
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'report',
        'hr_attendance',
        'attendance_change_request',
        'hr_attendance_ess',
        'hr_attendance_customization',
        'org_shift_timeline',
        'hr_attendance_report_xls'
    ],
    'data': [
        'wizard/employee_attendance_view.xml',
        'report/template.xml',
        'report/report_template.xml',
        'views/hr_attendance_reports.xml',
        'wizard/employee_attendance_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
}
