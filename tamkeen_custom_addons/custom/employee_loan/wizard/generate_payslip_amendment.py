from odoo import api, models, fields, _
from datetime import datetime, timedelta
from pytz import timezone


class GeneratePayslipAmendment(models.TransientModel):
    _name = 'loan.generate.payslip.amendment'

    hr_payroll_period_id = fields.Many2one('hr.payroll.period',
                                           string='Payroll Period')
    amendment_status = fields.Selection([('draft', 'Draft'),
                                         ('validate', 'Confirm')])
    remark = fields.Text('Remark')

    def riyadh_timezone(self, date):
        gmt_tz = timezone('GMT')
        if self.env.user and self.env.user.tz:
            local_tz = timezone(self.env.user.tz)
        else:
            local_tz = timezone('Asia/Riyadh')
        if date:
            gmt_utcdt = (gmt_tz.localize(date))
            riyadh_dt = gmt_utcdt.astimezone(local_tz)
            return riyadh_dt
        return date

    @api.model
    def default_get(self, default_fields):
        res = super(GeneratePayslipAmendment, self).default_get(default_fields)
        payroll_period_obj = self.env['hr.payroll.period']
        today_date = datetime.today()
        first_date_of_month = today_date.replace(day=1)
        lastMonth_date = first_date_of_month - timedelta(days=1)
        latest_payroll_period_id = payroll_period_obj.search([
            ('state', 'in', ('open', 'ended')), ('date_start', '>=',
                                                 str(lastMonth_date))],
            order="date_start",
            limit=1)
        res.update({'hr_payroll_period_id': latest_payroll_period_id.id})
        return res

    @api.multi
    def generate_amendment(self):
        employee_installment_obj = self.env['loan.installments']
        payslip_amendment_obj = self.env['hr.payslip.amendment']
        context = dict(self._context)
        if context and context.get('active_ids'):
            employee_installment_rec = \
                employee_installment_obj.browse(context.get('active_ids'))
            for installment in employee_installment_rec:
                policy_rec = \
                    installment.loan_id.loan_approval_policy_id
                vals = {
                    'type': 'deduction',
                    'employee_id':
                        installment.employee_id.id,
                    'name': 'Pay Slip Amendment: Employee Loan',
                    'loan_installment_id': installment.id,
                    'pay_period_id': self.hr_payroll_period_id.id,
                    'input_id': policy_rec.employee_loan_rule_input.id if
                    policy_rec.employee_loan_rule_input else False,
                    'amount': installment.amount,
                    'state': self.amendment_status,
                    'note': self.remark,
                }
                payslip_amendment_rec = payslip_amendment_obj.create(vals)
                installment.write({'state': 'amendment_created',
                                   'amendment_id': payslip_amendment_rec.id})
            self.env['loan.installments'].get_payslip_amendment()
