# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'COC Configuration',
    'version': '0.1',
    'category': 'Certificate of Comp',
    'description': """
    COC Configuration
""",
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com/',
    'depends': [
        'certificate_of_completion', 'service_configuration_panel', 'purchase',
    ],
    'data': [
        'views/coc_menu.xml',
        'views/templates.xml',
        'views/coc_view.xml',
        'views/res_company_view.xml',
        'wizard/coc_configuration_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
