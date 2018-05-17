{
    'name': 'Accrual',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """
Accruals
========
An Accrual is any benefit (usually time)
that accrues on behalf of an employee over an extended
period of time. This can be vacation days,
 sick days, or a simple time bank. The actual policy
and mechanics of accrual should be handled by
 other modules. This module only provides
the basic framework for recording the data.
    """,
    'author': 'Bista Solutions',
    'website': 'http://bistasolutions.com',
    'depends': [
        'hr',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_accrual_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
