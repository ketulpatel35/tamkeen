# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProjectMilestonesSchedule(models.Model):
    _inherit = 'project.milestones.schedule'

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        res = super(ProjectMilestonesSchedule, self).create(vals)
        if res.project_id and res.project_id.user_id:
            uid = self.env.user.id
            if uid != res.project_id.user_id.id:
                raise ValidationError(
                    _('Only the primary project manager can update the '
                      'related project information.'))
        return res

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        uid = self.env.user.id
        for rec in self:
            if rec.project_id and rec.project_id.user_id:
                if uid != rec.project_id.user_id.id:
                    raise ValidationError(
                        _('Only the primary project manager can update the '
                          'related project information.'))
        return super(ProjectMilestonesSchedule, self).write(vals)
