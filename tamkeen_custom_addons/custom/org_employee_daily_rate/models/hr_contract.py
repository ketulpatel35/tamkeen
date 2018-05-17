# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.depends('wage')
    def compute_daily_rate(self):
        """
        :return:
        """
        for rec in self:
            if rec.wage:
                rec.daily_rate = rec.wage / 30

    daily_rate = fields.Float('Daily Rate', compute='compute_daily_rate')