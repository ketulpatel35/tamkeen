# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "CRM Customization",
    "summary": "Manage all CRM related customization",
    "version": "1.0",
    "category": "CRM",
    "author": "Tamkeen Tech",
    "website": "https://tamkeentech.sa",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        'crm', 'sales_team', 'sale', 'res_partner_extension'
    ],
    "data": [
        'security/ir_group_view.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/template_view.xml',
        'views/crm_lead_view.xml',
        'views/sale_team_view.xml',
        'views/menu_view.xml'
    ],
}
