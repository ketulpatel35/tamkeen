# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Requisition ess',
    'version': '1.1',
    'category': 'Purchase Management',
    'depends': [
        'emp_self_services',
        'purchase_requisition_config',
        'hr_dashboard'
    ],
    'author': 'Bista Solutions',
    'description': """
This module is for the specification of Takamol technologie purchase.
=========================================================
    """,
    'data': [
        'views/pr_view.xml',
        'views/pr_menu.xml',
        'views/hr_dashboard_load.xml',
    ],
    'qweb': [
        "static/src/xml/hr_dashboard.xml",
    ],
    'installable': True,
    'auto_install': False
}
