# -*- coding: utf-8 -*-
from odoo import api, models


class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def create(self, vals):
        """
        on creation of project we unactivated analytic account
        :param vals:
        :return:
        """
        res = super(Project, self).create(vals)
        if res.analytic_account_id:
            # add reference as project code
            res.analytic_account_id.code = res.code
            # call method for inactive analytic account.
            res.analytic_account_id.toggle_active()
        return res