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
        bp_req_to_approve = self.env['org.benefits.program'].search_count(
            ['|', '&', ('employee_id.bp_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.bp_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.bp_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')
             ])
        is_bprta = self._check_group([
            'org_benefits_program.group_bp_manager_approval',
            'org_benefits_program.group_bp_vp_approval',
            'org_benefits_program.group_bp_ceo_approval'])
        if res:
            res[0]['benefits_program_request_to_approve'] = bp_req_to_approve
            res[0]['is_bprta'] = is_bprta
        return res