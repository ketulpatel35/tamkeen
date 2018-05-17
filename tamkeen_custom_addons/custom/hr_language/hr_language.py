# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo import tools


class hr_language(models.Model):
    _name = 'hr.language'

    name = fields.Selection(tools.scan_languages(), string='Language')
    description = fields.Char(string='Description', size=64, translate=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    can_read = fields.Boolean(string='Read', default=True)
    can_write = fields.Boolean(string='Write', default=True)
    can_speak = fields.Boolean(string='Speak',  default=True)


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    language_ids = fields.One2many('hr.language', 'employee_id',
                                   string='Languages')
