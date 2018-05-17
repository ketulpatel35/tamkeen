from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        uid = self.env.user.id
        for rec in self:
            if rec.user_id:
                if uid != rec.user_id.id:
                    raise ValidationError(
                        _('Only the primary project manager can update the '
                          'related project information.'))
        return super(Project, self).write(vals)
