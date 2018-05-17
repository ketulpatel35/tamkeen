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
# U1018
{
    'name': 'Skip Leaves Notifications',
    'version': '1.0',
    'author': 'Tamkeen ERP Team',
    'website': '',
    'category': 'Leave/Notifications',
    'description': """
    It gives the system more
     control on sending the leaves notifications.
    """,
    'depends': [
        'base',
        'base_action_rule',
        'hr_holidays_extension',
    ],
    'data': [
        'hr_holidays_view.xml',
        # 'templates.xml',
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
    'application': True
}
