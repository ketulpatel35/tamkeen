from odoo import api, models, fields, _
from datetime import datetime, timedelta
from pytz import timezone
from odoo.exceptions import UserError


class GeneratePayslipAmendment(models.TransientModel):
    _name = 'generate.payslip.amendment'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    payroll_period_id = fields.Many2one('hr.payroll.period', 'Payroll Period')
    amendment_status = fields.Selection([('draft', 'Draft'),
                                         ('validate', 'Confirm')])
    remark = fields.Text('Remark')

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        set domain
        :return:
        """
        res = {}
        res.update({'payroll_period_id': [('state', 'in', ['open', 'ended'])]})
        return {'domain': res}

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
        res.update({'payroll_period_id': latest_payroll_period_id.id})
        return res

    @api.multi
    def generate_amendment(self):
        overtime_statement_request_obj = self.env['overtime.statement.request']
        payslip_amendment_obj = self.env['hr.payslip.amendment']
        context = dict(self._context)
        if context and context.get('active_id'):
            overtime_statement_request_rec = \
                overtime_statement_request_obj.browse(context.get('active_id'))
            policy_rec = \
                overtime_statement_request_rec.overtime_claim_policy_id
            if policy_rec and policy_rec.overtime_salary_rule_input:
                vals = {
                    'type': 'addition',
                    'employee_id': self.employee_id.id,
                    'name': 'Pay Slip Amendment: Overtime',
                    'overtime_request_id': context.get('active_id'),
                    'pay_period_id': self.payroll_period_id.id,
                    'input_id': policy_rec.overtime_salary_rule_input.id,
                    'amount': overtime_statement_request_rec.total_day_cost,
                    'state': self.amendment_status,
                    'note': self.remark,
                }
                payslip_amendment_obj.create(vals)
                overtime_statement_request_rec.service_validate12()
            else:
                raise UserError(_('You need to configure Overtime Salary '
                                  'Rule Input in policy.'))
