# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'fix contract duplicate',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """

    """,
    'author': 'Tamkeen Team',
    'website': 'http://www.tamkeentech.sa',
    'depends': [
        'hr',
        'hr_employee_state',
        'hr_contract_init'
    ],
    'init_xml': [
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups.xml',
        # 'hr_contract_init_workflow.xml',
        'hr_contract_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
