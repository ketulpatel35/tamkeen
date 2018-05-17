# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Business Unit',
    'version': '1.0',
    'category': 'Business Unit',
    'sequence': 15,
    'summary': 'Business Unit',
    'description': """

    """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['purchase', 'account', 'sale', 'purchase_requisition',
                'purchase_requisition_config'],
    'data': [
            'security/hr_security.xml',
            'security/ir.model.access.csv',
            # 'views/business_unit_view.xml',
            'views/sale_view.xml',
            'views/purchase_view.xml',
            'views/stock_view.xml',
            'views/customer_invoice_view.xml',
            'views/account_invoice_view.xml',
            'views/account_move_view.xml',
            'views/payment_view.xml',
            # 'views/department_view.xml',
            # 'views/division_view.xml',
            'views/costcenter_view.xml',
            'views/pr_email_template_view.xml',
            # 'views/section_view.xml',
            'views/purchase_requisition_view.xml',
    ],
    'demo': [

    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
