# -*- coding: utf-8 -*-
##############################################################################

{
    'name': 'Product Extension',
    'version': '1.0',
    'author': 'bistasolutions',
    'category': '',
    'description': """
This addon to:
#############################
- Add security groups to procuremnt.
    """,
    'website': 'http://wwww.bistasolutions.com/',
    'depends': [
        'base', 'product', 'stock', 'purchase'
    ],
    'data': [
        'security/product_groups.xml',
        'security/ir.model.access.csv',
        'views/product_menu_view.xml',

    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
}
