from odoo import api, models, fields, _
from datetime import datetime, timedelta


class HSCGeneratePayslipAmendment(models.TransientModel):
    _name = 'hsc.generate.payslip.amendment'

    hr_payroll_period_id = fields.Many2one('hr.payroll.period',
                                           string='Payroll Period')
    input_id = fields.Many2one('hr.rule.input', 'Salary Rule Input')
    amendment_status = fields.Selection([('draft', 'Draft'),
                                         ('validate', 'Confirm')])
    remark = fields.Text('Remark')

    @api.model
    def default_get(self, default_fields):
        res = super(HSCGeneratePayslipAmendment, self).default_get(
            default_fields)
        payroll_period_obj = self.env['hr.payroll.period']
        today_date = datetime.today()
        first_date_of_month = today_date.replace(day=1)
        lastMonth_date = first_date_of_month - timedelta(days=1)
        latest_payroll_period_id = payroll_period_obj.search([
            ('state', 'in', ('open', 'ended')), ('date_start', '>=',
                                                 str(lastMonth_date))],
            order="date_start", limit=1)
        res.update({'hr_payroll_period_id': latest_payroll_period_id.id})
        return res

    @api.multi
    def generate_amendment(self):
        """
        :return:
        """
        salary_certificates_obj = self.env['emp.salary.certificates']
        payslip_amendment_obj = self.env['hr.payslip.amendment']
        context = dict(self._context)
        if context and context.get('active_ids'):
            salary_certificates_rec = \
                salary_certificates_obj.browse(context.get('active_ids'))
            if salary_certificates_rec:
                vals = {
                    'type': 'deduction',
                    'employee_id':
                        salary_certificates_rec.employee_id.id,
                    'name': 'Pay Slip Amendment: Employment Certificate',
                    'salary_certificates_id': salary_certificates_rec.id,
                    'pay_period_id': self.hr_payroll_period_id.id,
                    'input_id': self.input_id.id,
                    'amount': 25,
                    'state': self.amendment_status,
                    'note': self.remark,
                }
                payslip_amendment_rec = payslip_amendment_obj.create(vals)
                if self.amendment_status == 'validate':
                    payslip_amendment_rec.do_validate()
                salary_certificates_rec.payslip_amendment_id = \
                    payslip_amendment_rec.id
