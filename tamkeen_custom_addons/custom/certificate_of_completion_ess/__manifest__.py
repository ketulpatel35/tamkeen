# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    "name": "Certificate of Completion ESS",
    "version": "1.0",
    "description": "Certificate of Completion Employee Self Service",
    "author": "Bista Solutions",
    'website': 'www.bistasolutions.com',
    "depends": ['certificate_of_completion', 'procurment_requistion_ess',
                'purchase_requisition_config'],
    "category": "hr",
    "data": [
        'views/certificate_of_completion_view.xml',
        'views/menu_items_view.xml'
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
