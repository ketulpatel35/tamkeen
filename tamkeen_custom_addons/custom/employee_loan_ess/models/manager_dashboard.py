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
        loan_request_to_approve = self.env['hr.employee.loan'].search_count(
            ['|', '&', ('employee_id.loan_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.loan_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.loan_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')
             ])
        is_lrta = self._check_group([
            'employee_loan.group_loan_manager_approval'])
        if res:
            res[0]['loan_request_to_approve'] = loan_request_to_approve
            res[0]['is_lrta'] = is_lrta
        return res