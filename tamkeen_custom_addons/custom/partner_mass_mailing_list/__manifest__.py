# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    # Addon information
    'name': "Mass mailing from partners",
    'description': """
Mass mailing from partners
==========================

Add button to add to mailing lists.
    """,
    'category': 'CRM',
    'version': '1.0',
    # Dependencies
    'depends': [
        'mass_mailing',

    ],
    'external_dependencies': {},
    # Views templates, pages, menus, options and snippets
    'data': [
        'views/res_partner.xml',
        'wizard/partner_mail_list_wizard.xml'
    ],
    # Qweb templates
    'qweb': [
    ],
    # Your information
    'author': 'Bistasolutions.com',
    'maintainer': 'bistasolutions.com',
    'website': 'http://www.bistasolutions.com',
    'license': 'AGPL-3',
    # Technical options
    'demo': [],
    'test': [],
    'installable': True,
    # 'auto_install':False,
    # 'active':True,
}
