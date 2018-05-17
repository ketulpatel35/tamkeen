from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError


class CancelWizard(models.TransientModel):
    """Open wizard for cancel."""

    _name = "employee.objective.cancellation.wizard"
    _description = "Cancellation Wizard"

    can_remarks = fields.Char(string='Remarks')
    can_date = fields.Date(string='Date', default=datetime.today().date())

    @api.multi
    def create_request(self):
        model = self._context.get('active_model')
        obj = self.env[model].browse(self._context.get('active_id'))
        message = ''
        remark = ''
        for rec in obj:
            if rec.state == 'manager_approval':
                message = 'Manager Remarks:'
            if rec.remarks:
                remark = rec.remarks
            if self.can_remarks:
                rec.remarks = remark+"\n"+message + self.can_remarks
                rec.can_date = self.can_date
                rec.state = 'cancel'
            else:
                raise ValidationError(
                    _('Please fill the remarks'))
        return True
