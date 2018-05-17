{
    'name': 'HR Attendance ESS',
    'version': '1.0',
    'category': 'HR/Attendance',
    'description': """
    HR Attendance
    Attendance Employee Self service
    Manager Self Service
    Manager Dashboard
    """,
    'author': 'Tamkeen Technologies',
    'website': '',
    'depends': [
        'hr_attendance_customization',
        'emp_self_services',
        'hr_attendance',
        'attendance_change_request',
        'hr_dashboard'
    ],
    'data': [
        'views/hr_attendance_view.xml',
        'views/hr_attendance_ess_view.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'installable': True,
    'auto_install': False,
}
