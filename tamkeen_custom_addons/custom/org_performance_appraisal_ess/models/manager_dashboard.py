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
        pa_req_to_approve = self.env['performance.appraisal'].search_count(
            ['|', '&', ('employee_id.pa_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.pa_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.pa_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')
             ])
        is_bprta = self._check_group([
            'org_performance_appraisal.group_pa_manager_approval',
            'org_performance_appraisal.group_pa_vp_approval',
            'org_performance_appraisal.group_pa_ceo_approval'])
        if res:
            res[0]['performance_appraisal_request_to_approve'] = \
                pa_req_to_approve
            res[0]['is_bprta'] = is_bprta
        return res