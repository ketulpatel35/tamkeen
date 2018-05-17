{
    'name': 'Employee Shift Scheduling',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Employee Shift Scheduling
=========================

Easily create, manage, and track employee schedules.
    """,
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr_attendance',
        'hr_contract',
        'hr_contract_init',
        'hr_employee_state',
        'hr_holidays',
        'hr_admin',
        'mail',
        'hr',
        'hr_attendance_customization',
        'hr_employee_customization',
        'hr_payroll',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_schedule_data.xml',
        'views/hr_schedule_view.xml',
        'wizard/validate_schedule_view.xml',
        'wizard/compute_alerts_view.xml',
        'wizard/generate_schedules_view.xml',
        'wizard/restday_view.xml',
        'views/hr_schedule_data.xml',
        'views/hr_schedule_cron.xml',
        'views/alert_rule_data.xml',
    ],
    'installable': True,
    'active': False,
    'auto_install': False,
}
