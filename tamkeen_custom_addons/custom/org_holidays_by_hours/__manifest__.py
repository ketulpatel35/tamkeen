# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Org Holidays By User',
    'version': '1.1',
    'author': 'Bista Solutions',
    'category': 'Org Holidays By User',
    'description': """
    """,
    'depends': ['hr_holidays_extension', 'hr_payroll_period'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_holidays_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
