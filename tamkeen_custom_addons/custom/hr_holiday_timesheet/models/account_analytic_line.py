# -*- coding: utf-8 -*-
# © 2017 Jerome Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, api, models


class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    leave_id = fields.Many2one('hr.holidays', string='Related Leave')
