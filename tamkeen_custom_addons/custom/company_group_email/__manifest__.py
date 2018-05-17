# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Group Email',
    'version': '0.1',
    'category': 'Company',
    'description': """
Allow the comapny to add a group email to it's main shared services
departments.
""",
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'base',
    ],
    'data': [
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
