{
    'name': 'Employee Leave Summary',
    'version': '1.0',
    'category': 'Employee',
    'description': """
        Employee Leave Summary
    """,
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr',
        'hr_holidays',
        'hr_contract',
        'hr_admin',
        'hr_holidays_extension',
        # 'hr_policy_accrual',
        'emp_self_services',
        'erp_domain_name',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/templates.xml',
        # 'views/employee_leave_summar1y_cron.xml',
        # 'views/employee_leave_summary_view.xml',
        'views/hr_work_resumption_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
