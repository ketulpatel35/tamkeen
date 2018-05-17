# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Default Employee Approval Line',
    'version': '0.1',
    'category': 'HR/Approval',
    'description': """
Link/Reset the employee approval line.
""",
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'service_management',
        'hr_employee_marked_roles',
    ],
    'data': [
        'views/hr_employee_approval_line_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
