from odoo import models, api, fields, _
from odoo.exceptions import Warning


class employee_loan_remove_wizard(models.TransientModel):
    _name = 'employee.loan.remove.wizard'

    @api.multi
    def remove_loan(self):
        context = dict(self._context) or {}
        if context.get('active_id'):
            employee_loan_rec = self.env['hr.employee.loan'].browse(context.get(
                'active_id'))
            if employee_loan_rec.employee_id.user_id.id != self.env.user.id \
                    and employee_loan_rec.state != 'draft':
                raise Warning(_('Only requests in draft state can be removed.'))
            employee_loan_rec.unlink()
        return True