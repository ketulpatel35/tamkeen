# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    user_ref_ids = fields.Many2many('res.users', 'ref2', 'ref1', 'sales_person', string="User", invisible=1)


class CrmReport(models.TransientModel):
    _name = 'crm.won.lost.report'

    sales_person = fields.Many2many('res.users', 'ref1', 'ref2', 'user_ref_ids', string="Sales Persons")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', default=fields.Date.today)

    @api.multi
    def print_xls_report(self):
        data = self.read()[0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'crm_won_lost_report.report_crm_won_lost_report.xlsx',
                'datas': data
                }

