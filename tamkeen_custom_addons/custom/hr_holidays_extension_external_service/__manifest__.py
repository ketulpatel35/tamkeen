{
    'name': 'Hr holidays Extension External Service',
    'version': '1.0',
    'category': 'HRMS',
    'description': """
    """,
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_holidays_extension',
    ],
    'data': [
        'data/external_portal_data.xml',
        'views/hr_employee_view.xml',
        'views/hr_holidays_view.xml',
        'views/template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
