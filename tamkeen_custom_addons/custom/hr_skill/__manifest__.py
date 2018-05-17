# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    "name": "Skill Management",
    "version": "10.0",
    "category": "Human Resources",
    "license": "AGPL-3",
    "description": """
    This module allows you to manage your company and employees skills.
    """,
    "author": "Bista solutions",
    "website": "http://www.bistasolutions.com",
    "depends": ["hr", "emp_self_services"],
    'data': [
        "security/ir.model.access.csv",
        'security/ir_rule.xml',
        "views/hr_skill_view.xml",
        "views/templates.xml",
        "views/menu_view.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "auto_install": False,
    "images": [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
