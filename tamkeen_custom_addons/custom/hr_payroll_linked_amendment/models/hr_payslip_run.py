from odoo import models, api, _
from datetime import date
from odoo.exceptions import Warning


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def confirm_payslip_run(self):
        for rec in self:
            if not rec.slip_ids:
                raise Warning(_('You should have draft payslips to confirm.'))
            for payslip in rec.slip_ids:
                payslip.action_payslip_done()
            rec.payroll_period_id.write({'last_payroll_run_date':
                                             date.today(), 'state': 'closed'})
        return True

    @api.multi
    def compute_the_payslip(self):
        for rec in self:
            if not rec.slip_ids:
                raise Warning(_('You should have draft payslips to Compute.'))
            from_date = rec.date_start
            to_date = rec.date_end
            amendment_code = []
            for payslip in rec.slip_ids:
                slip_data = payslip.onchange_employee_id(from_date,
                                                             to_date,
                                             payslip.employee_id.id,
                                             payslip.employee_id.contract_id.id)
                worked_days_line_ids = [slip_data['value'].get(
                    'worked_days_line_ids')]
                input_line_ids = [slip_data['value'].get(
                    'input_line_ids')]
                for worked_days_lines in payslip.worked_days_line_ids:
                    for new_worked_days_line in worked_days_line_ids[0]:
                        if worked_days_lines.code == \
                                new_worked_days_line.get('code'):
                            worked_days_lines.write(
                                {'number_of_days':
                                     new_worked_days_line.get('number_of_days'),
                                    'number_of_hours':
                                        new_worked_days_line.get('number_of_hours')
                                            })
                input_lst = []
                for line in payslip.input_line_ids:
                    amendment_code.append(line.code)
                for input in input_line_ids[0]:
                    if input.get('code') not in amendment_code:
                        input_data = {
                            'name': input.get('name'),
                            'code': input.get('code'),
                            'contract_id': input.get('contract_id'),
                            'amount': input.get('amount')
                        }
                        input_lst.append((0, 0, input_data))
                for input_line in payslip.input_line_ids:
                    for input in input_line_ids[0]:
                        if input_line.code == input.get('code'):
                            input_line.write({'amount': input.get('amount')})
                payslip.write({'input_line_ids': input_lst})
                payslip.compute_sheet()