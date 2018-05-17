# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Technologies
#    Copyright (C) 2016 (http://http://www.tamkeentech.sa/en)
#
##############################################################################

{
    'name': 'Attendance Report Excel',
    'version': '1.0',
    'category': 'Attendance',
    'description': """
    """,
    'author': 'Tamkeen Technologies',
    'website': 'http://http://www.tamkeentech.sa',
    'depends': [
        'report',
        'hr_attendance',
        'attendance_change_request',
        'hr_attendance_customization'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_department_xls.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
}
