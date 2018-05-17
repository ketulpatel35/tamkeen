# -*- coding: utf-8 -*-
##############################################################################

{
    'name': 'Partner Extension',
    'version': '1.0',
    'author': 'bistasolutions',
    'category': '',
    'description': """
This addon to:
#############################
- Add more fields to help the user to get more information about the partners.
    """,
    'website': 'http://wwww.bistasolutions.com/',
    'depends': [
        'base', 'account', 'project', 'hr_recruitment', 'contacts',
        'purchase','vendor_registration','ksa_vat'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'res_partner_view.xml',
        'views/res_partner_menu.xml',
        'views/template.xml',
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
}
