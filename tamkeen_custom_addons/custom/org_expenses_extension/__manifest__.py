# -*- encoding: utf-8 -*-
##############################################################################
#
#    Tamkeen Tech
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Organization Expense Management",
    'summary': 'Expense Management',
    'description': """
    """,
    'category': 'Expense Management',
    'version': '1.0',
    'depends': [
        'hr_expense',
        'service_configuration_panel',
        'organization_structure',
        'hr_employee_approval_tab',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/hr_expense_view.xml',
        'views/hr_employee_view.xml',
        'views/templates.xml',
        'views/expense_configuration.xml',
        'views/menu_view.xml',
        'views/expense_sequence.xml',
        'security/ir_rule.xml',
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Tamkeen Tech',
    'maintainer': 'tamkeentech.sa',
    'website': 'http://tamkeentech.sa',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
}
