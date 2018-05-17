# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Approval Matrix",
    "version": "1.0",
    "description": "Approval Matrix",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['base', 'hr', 'mail'],
    "category": "hr",
    "data": [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/dam_manage_view.xml',
        'views/dam_history_view.xml',
        'views/stage_configuration_view.xml',
        'views/set_delegation_view.xml',
        'wizard/user_selection_view.xml',
        'views/menu_view.xml',
    ],
    "installable": True,
}
