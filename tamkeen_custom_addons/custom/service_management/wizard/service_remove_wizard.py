from odoo import models, api, fields, _
from odoo.exceptions import Warning


class service_remove_wizard(models.TransientModel):
    _name = 'service.remove.wizard'

    @api.multi
    def remove_service(self):
        context = dict(self._context) or {}
        if context.get('active_id'):
            service_rec = self.env['service.request'].browse(context.get(
                'active_id'))
            if service_rec.employee_id.user_id.id != self.env.user.id \
                    and service_rec.state != 'draft':
                raise Warning(_('Only requests in draft state can be removed.'))
            service_rec.unlink()
        return True