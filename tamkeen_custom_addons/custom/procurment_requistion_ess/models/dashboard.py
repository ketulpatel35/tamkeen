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
        pr_to_approve = self.env[
            'purchase.requisition'].search_count(
            [('state', 'in', ['ceo', 'tomanager_app', 'vp'])])
        is_prta = self._check_group([
            'purchase_requisition_config.group_manager_approval_pr',
            'purchase_requisition_config.group_vp_approval_pr',
            'purchase_requisition_config.group_ceo_approval_pr'])
        if res:
            res[0]['procurement_requisition_to_approve'] = pr_to_approve
            res[0]['is_prta'] = is_prta
        return res