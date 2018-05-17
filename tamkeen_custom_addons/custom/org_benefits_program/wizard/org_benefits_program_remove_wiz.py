from odoo import models, api, fields, _
from odoo.exceptions import Warning


class OrgBenefitsProgramRemoveWiz(models.TransientModel):
    _name = 'org.benefits.program.remove.wiz'

    @api.multi
    def remove_service(self):
        context = dict(self._context) or {}
        if context.get('active_ids'):
            service_rec = self.env['org.benefits.program'].browse(context.get(
                'active_ids'))
            for rec in service_rec:
                if rec.employee_id.user_id.id != self.env.user.id \
                        or rec.state != 'draft':
                    raise Warning(
                        _('Only requests in draft state can be removed.'))
                rec.unlink()
        return True
