from odoo import models, api, fields, _
from odoo.exceptions import Warning


class employee_leave_remove_wizard(models.TransientModel):
    _name = 'employee.leave.remove.wizard'

    @api.multi
    def remove_leave(self):
        context = dict(self._context) or {}
        if context.get('active_id'):
            holiday_rec = self.env['hr.holidays'].browse(context.get(
                'active_id'))
            if holiday_rec.employee_id.user_id.id != self.env.user.id \
                    and holiday_rec.state != 'draft' and holiday_rec.amend \
                    == False:
                raise Warning(_('Only requests in draft state can be removed.'))
            holiday_rec.unlink()
        return True