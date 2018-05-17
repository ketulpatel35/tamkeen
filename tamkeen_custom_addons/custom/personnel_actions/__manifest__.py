{
    'name': 'Personnel Actions',
    'version': '1.0',
    'category': 'Personnel Actions',
    'description': """
    Personnel Actions
    """,
    'author': 'Bista Solutions',
    'website': '',
    'depends': [
        'hr', 'organization_structure',
        'hr_contract', 'web_readonly_bypass',
        'org_structure_payroll',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/personnel_action_view.xml',
        'views/personnel_action_type_view.xml',
        'views/ir_sequence.xml',
        'views/hr_position_view.xml',
        'views/hr_employee_view.xml',
        'views/menu_view.xml',
        # 'views/hr_contract_view.xml',
        'wizard/manual_acive_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
