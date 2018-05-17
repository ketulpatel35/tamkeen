# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class HrDashboard(models.Model):
    _inherit = 'hr.dashboard'

    @api.model
    def get_employee_info(self):
        """
        get recruitment data on dashboard
        :rtype dict
        :return: data
        """
        res = super(HrDashboard, self).get_employee_info()
        is_recruitment = self._check_group([
            'hr_recruitment_stages_movement.group_dep_manager',
            'hr_recruitment.group_hr_recruitment_manager'])
        if res:
            res[0]['is_recruitment'] = is_recruitment
        return res