# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'HR Payroll ESS',
    'category': 'Payroll',
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'version': '1.0',
    'description': """
    The Employee can see his/her payslip.
    """,
    'depends': [
        'hr_payroll_customization',
        'emp_self_services',
        'hr_dashboard',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll_view.xml',
        'views/menu_view.xml',
        'views/manager_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'active': True,
    'installable': True,
}
