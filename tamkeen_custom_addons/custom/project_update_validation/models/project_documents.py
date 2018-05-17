from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import Warning, ValidationError

class ProjectDocuments(models.Model):
    _inherit = 'project.documents'

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        res = super(ProjectDocuments, self).create(vals)
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
        return super(ProjectDocuments, self).write(vals)