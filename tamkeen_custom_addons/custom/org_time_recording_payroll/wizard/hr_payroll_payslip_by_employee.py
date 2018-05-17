from odoo import api, fields, models, _
from odoo.exceptions import Warning


# class HrPayslipEmployees(models.TransientModel):
#     _inherit = 'hr.payslip.employees'
#     _description = 'Generate payslips for all selected employees'
#
#     @api.multi
#     def compute_sheet(self):
#         payroll_period_id = False
#         if self.env.context.get('active_id'):
#             payroll_period_id = self.env['hr.payslip.run'].browse(
#                 self.env.context.get('active_id')).payroll_period_id.id
#         return super(HrPayslipEmployees,
#                      self.with_context(payroll_period_id=payroll_period_id)).compute_sheet()


class HrAdjustedHours(models.TransientModel):
    _name = 'hr.adjusted.hours'
    _description = 'Adjusted Hours'

    @api.multi
    def button_adjusted_hours(self):
        context = dict(self._context)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        active_ids = context.get('active_ids')
        time_date = ''
        for line in time_recording_line_obj.browse(active_ids):
            if line.state not in ('draft', 'new_joiner'):
                time_date += str(line.date) + ', '
        if time_date:
            raise Warning(_('The records already confirmed, To do so '
                            'you need to return it back to the '
                            'previous state.\n %s')
                          % time_date)
        for line in time_recording_line_obj.browse(active_ids):
            line.write({'adjusted_hours': line.absence_hours})
