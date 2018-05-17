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
        get leave data on dashboard
        :rtype dict
        :return: data
        """
        res = super(HrDashboard, self).get_employee_info()
        uid = request.session.uid
        leaves_to_approve = self.env['hr.holidays'].search_count([
            ('type', '=', 'remove'),
            ('state', 'in', ['ceo', 'vp', 'confirm']), '|',
            ('employee_id.leave_manager_id.user_id.id', '=', uid), '|',
            ('employee_id.leave_vp_id.user_id.id', '=', uid),
            ('employee_id.leave_ceo_id.user_id.id', '=', uid)])
        access_leave_manager = self._check_group([
            'hr_holidays_extension.group_leave_bu_manager_approval'])
        if res:
            res[0]['leaves_to_approve'] = leaves_to_approve
            res[0]['access_leave_manager'] = access_leave_manager
        return res