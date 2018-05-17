# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api
from odoo.http import request


class HrDashboard(models.Model):
    _inherit = 'hr.dashboard'

    @api.model
    def get_employee_info(self):
        """
        get overtime data on dashboard
        :rtype dict
        :return: data
        """
        res = super(HrDashboard, self).get_employee_info()
        uid = request.session.uid
        ot_pre_req_to_approve = self.env[
            'overtime.pre.request'].search_count(
            ['|', '&',
             ('employee_id.overtime_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.overtime_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.overtime_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')])
        overtime_claims_to_approve = self.env[
            'overtime.statement.request'].search_count(
            ['|', '&',
             ('employee_id.overtime_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.overtime_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.overtime_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')])
        is_otrta = self._check_group([
            'hr_overtime.group_overtime_manager_approval'])
        if res:
            res[0]['overtime_pre_requests_to_approve'] = ot_pre_req_to_approve
            res[0]['overtime_claims_to_approve'] = overtime_claims_to_approve
            res[0]['is_otrta'] = is_otrta
        return res