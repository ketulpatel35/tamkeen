# -*- coding: utf-8 -*-
##############################################################################

##############################################################################

{
    'name': 'Attendance Capture',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance'],
    'author': 'Tamkeen Team',
    'description': """
    """,
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/attendance_capture_view.xml',
        'views/hr_employee_attendance_view.xml',
        'views/attendance_cron_job.xml',
    ],

    'installable': True,
    'auto_install': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
