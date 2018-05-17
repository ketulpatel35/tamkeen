from odoo import api, fields, models, _


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    @api.multi
    def compute_sheet(self):
        payroll_period_id = False
        if self.env.context.get('active_id'):
            payroll_period_id = self.env['hr.payslip.run'].browse(
                self.env.context.get('active_id')).payroll_period_id.id
        return super(HrPayslipEmployees,
                     self.with_context(payroll_period_id=payroll_period_id)).compute_sheet()