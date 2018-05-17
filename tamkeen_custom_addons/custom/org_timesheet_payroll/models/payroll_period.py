from odoo import models, fields, api, _
from datetime import date


class HrPayrollPeriod(models.Model):
    _inherit = 'hr.payroll.period'

    def _get_start_end_date(self):
        start_date = str(self.date_form).split(' ')[0]
        end_date = str(self.date_to).split(' ')[0]
        return start_date, end_date

    def lock_recording_timesheet(self):
        start_date, end_date = self._get_start_end_date()
        timehsheet_recording_rec = self.env[
            'sheet.time.recording.line'].search([
            ('date', '>=', start_date), ('date', '<=', end_date)])
        for recording in timehsheet_recording_rec:
            recording.write({'payroll_locked': True, 'payroll_locked_date':
                date.Today()})
        return True

    @api.multi
    def set_state_locked(self):
        res = super(HrPayrollPeriod, self).set_state_locked()
        for rec in self:
            rec.lock_recording_timesheet()
        return res