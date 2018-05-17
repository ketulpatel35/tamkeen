# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    def _compute_self_update(self):
        current_user_id = self.env.user
        for emp in self:
            current_employee = False
            if current_user_id.id == emp.user_id.id:
                current_employee = True
            emp.is_current_employee = current_employee

    is_current_employee = fields.Boolean(string="Employee Self Update", compute=_compute_self_update, invisible=True)
