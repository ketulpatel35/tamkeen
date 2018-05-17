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
        req_to_approved = self.env[
            'attendance.change.request'].search_count([
            ('state', 'in', ['for_review']),
            ('employee_id.attendance_manager_id.user_id.id', '=', uid)])
        access_attendance_manager = self._check_group([
            'hr_attendance.group_hr_attendance_manager'])
        if res:
            res[0]['attendance_change_req_to_approved'] = req_to_approved
            res[0]['access_attendance_manager'] = access_attendance_manager
        return res