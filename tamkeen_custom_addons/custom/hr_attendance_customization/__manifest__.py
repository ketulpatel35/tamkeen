{
    'name': 'HR Attendance Customization',
    'version': '1.0',
    'category': 'HR/Attendance',
    'description': """
    HR Admin Groups
    """,
    'author': 'Tamkeen Technologies',
    'website': '',
    'depends': [
        'hr_attendance',
        'hr_timesheet_attendance',
        'hr_employee_approval_tab'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/attendance_configuration.xml',
        'views/hr_attendance_view.xml',
        'views/hr_employee_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
