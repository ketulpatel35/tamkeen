# -*- coding: utf-8 -*-
##############################################################################

##############################################################################

{
    'name': 'Attendance Change Request',
    'version': '1.0',
    'depends': ['hr',
                'hr_attendance',
                'attendance_capture',
                'hr_employee_customization',
                'hr_attendance_customization',
                ],
    'author': 'Tamkeen Technologies',
    'description': """
    1. Employee will submit Change Request to immediate manager.
    2. Employee will choose one of the attendance reasons excuse that is
    shown in a drop down list ( the predefined list is shown below).\n
    3. Immediate manager can either approve or reject (with remarks mandatory).
    4. Hr manager can either approve or reject employee's request.
    5. if employee is on leave, system should not consider as absent in the
    attendance reporting / analysis. it should be marked as "Leave"
    """,
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/attendance_change_request.xml',
        'views/hr_attendance_history.xml',
        'views/menu_items_view.xml',
        'views/templates.xml'
    ],
    'installable': True,
    'auto_install': False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
