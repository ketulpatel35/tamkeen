# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Purchase Requisition Configuration',
    'version': '1.1',
    'category': 'Purchase Management',
    'depends': [
        'purchase_requisition',
        'base_action_rule',
        'account',
        'hr_admin',
        'purchase_config',
        'purchase',
        'analytic',
        'erp_domain_name',
        'hr_employee_approval_tab',
    ],
    'author': 'Bista Solutions',
    'description': """
This module is for the specification of Takamol technologie purchase.
=========================================================
    """,
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'wizard/po_requisition_wiz_view.xml',
        'views/purchase_requisition_view.xml',
        'views/purchase_req_acc.xml',
        'views/company_view.xml',
        'views/p_r_analytic_mandatory.xml',
        'views/hr_employee_view.xml',
        # 'views/purchase_requisition_approval.xml',
    ],
    'installable': True,
    'auto_install': False,
}
