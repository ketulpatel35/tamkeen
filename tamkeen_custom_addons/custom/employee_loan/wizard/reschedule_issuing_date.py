from odoo import api, models, fields, _
from datetime import date
from odoo.exceptions import Warning


class RescheduleIssuingDate(models.TransientModel):
    _name = 'reschedule.issuing.date'

    reschedule_due_date = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')], string='Reschedule '
                                                               'Due Date')
    loan_issuing_date = fields.Date(string='Loan Issuing Date')

    def _check_feature_date(self):
        today_date = date.today()
        if self.loan_issuing_date > str(today_date):
            raise Warning(_('You can not select future date.'))
        return True

    @api.multi
    def button_confirm(self):
        context = self._context or {}
        if context and context.get('active_id'):
            loan_rec = self.env['hr.employee.loan'].browse(context.get(
                'active_id'))
            if self.reschedule_due_date == 'no':
                self._check_feature_date()
            loan_rec.button_confirm(self.loan_issuing_date, self.reschedule_due_date)
        return True
