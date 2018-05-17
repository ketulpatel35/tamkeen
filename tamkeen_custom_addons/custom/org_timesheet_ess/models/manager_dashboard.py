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
        timesheets_to_approve = self.env[
            'hr_timesheet_sheet.sheet'].search_count(
            ['|', ('employee_id.timesheet_manager_id.user_id.id', '=', uid),
             '|', ('employee_id.timesheet_vp_id.user_id.id', '=', uid),
             ('employee_id.timesheet_ceo_id.user_id.id', '=', uid)])
        timesheet_search_view_id = self.env.ref(
            'hr_timesheet_sheet.view_hr_timesheet_sheet_filter')
        if res:
            res[0]['timesheets_to_approve'] = timesheets_to_approve
            res[0]['timesheet_search_view_id'] = timesheet_search_view_id.id
        return res