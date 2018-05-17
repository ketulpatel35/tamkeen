{
    'name': 'Auto Fill Employee Approval Line',
    'version': '1.0',
    'category': 'Employee',
    'description': """
    When User select the service manager,vp,ceo automatic all
    approval/delegation have same value.
    """,
    'author': 'Bista Solutions',
    'website': '',
    'depends': [
        'hr',
        'hr_holidays_extension',
        'employee_loan',
        'hr_overtime',
        'org_timesheet_extension',
        'org_expenses_extension',
    ],
    'data': [
    ],
    'installable': True,
    'auto_install': False,
}
