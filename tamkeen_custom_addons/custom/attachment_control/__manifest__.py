# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Attachment Control',
    'version': '1.0',
    'depends': ['hr', 'account_analytic_default',
                'hr_timesheet_sheet', 'hr_payroll', 'hr_attendance',
                'purchase_requisition', 'purchase', 'product', 'stock',
                'hr_admin', 'sales_team'
                ],
    'author': 'Openinside co.',
    'description': """
    """,
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
