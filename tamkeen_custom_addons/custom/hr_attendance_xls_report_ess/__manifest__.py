{
    'name': 'Attendance Excel Report for Manager/VP',
    'version': '1.0',
    'category': 'Attendance',
    'description': """
        * This module used for add Print Attendance XLS Menu in Manager Self
        Service for Manager/VP.
        * Filter by Department of Manager and also considder child
        departments of login manager and Print the Attendance XLS
        Report.
    """,
    'author': 'Tamkeen Technologies',
    'website': 'http://www.tamkeentech.sa/',
    'depends': [
        'emp_self_services',
        'hr_attendance_report_xls'
    ],
    'data': [
        'views/manager_attendance_view.xml'
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
}
