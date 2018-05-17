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
        get general services data on dashboard
        :rtype dict
        :return: data
        """
        res = super(HrDashboard, self).get_employee_info()
        uid = request.session.uid
        gs_req_to_approve = self.env[
            'service.request'].search_count(
            ['|', '&', ('employee_id.service_manager_id.user_id.id', '=', uid),
             ('state', '=', 'mngr_approval'), '|', '&',
             ('employee_id.service_vp_id.user_id.id', '=', uid),
             ('state', '=', 'vp_approval'), '&',
             ('employee_id.service_ceo_id.user_id.id', '=', uid),
             ('state', '=', 'ceo_approval')
             ])
        access_service_manager = self._check_group(
            ['service_management.group_service_bu_manager_approval'])
        if res:
            res[0]['general_services_requests_to_approve'] = gs_req_to_approve
            res[0]['access_service_manager'] = access_service_manager
        return res