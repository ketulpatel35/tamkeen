{
    'name': 'Personnel Actions Leave',
    'version': '1.0',
    'category': 'Personnel Actions Leave',
    'description': """
    Personnel Actions
    """,
    'author': 'Bista Solutions',
    'website': '',
    'depends': [
        'personnel_actions', 'hr_holidays_extension'
    ],
    'data': [
        'views/personnel_action_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
