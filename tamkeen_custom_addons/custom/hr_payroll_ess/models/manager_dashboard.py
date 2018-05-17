# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api
from odoo.http import request
import datetime


class HrDashboard(models.Model):
    _inherit = 'hr.dashboard'

    @api.model
    def get_employee_info(self):
        """
        get attendance data on dashboard
        :rtype dict
        :return: data
        """
        res = super(HrDashboard, self).get_employee_info()
        uid = request.session.uid
        employee_payslip = self.env['hr.payslip'].search_count([
            ('employee_id.user_id.id', '=', uid),
            ('employee_id.parent_id.user_id.id', '=', uid)])
        is_eps = self._check_group([
            'hr_payroll_ess.group_manager_approval'])
        if res:
            res[0]['employee_payslip'] = employee_payslip
            res[0]['is_eps'] = is_eps
        return res