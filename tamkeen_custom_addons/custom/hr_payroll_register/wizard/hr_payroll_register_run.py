# -*- coding:utf-8 -*-
from datetime import datetime
from pytz import timezone
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OEDATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OEDATE_FORMAT


class PayrollRegisterRun(models.TransientModel):
    _name = 'hr.payroll.register.run'
    _description = 'Pay Slip Creation'

    department_ids = fields.Many2many('hr.department',
                                      'hr_department_payslip_run_rel',
                                      'register_id', 'register_run_id',
                                      'Organization Unit')

    @api.multi
    def create_payslip_runs(self):
        """
        create Payslips Batches and genarate Employee Payslips
        :return:
        """
        hr_employee_obj = self.env['hr.employee']
        hr_payslip_obj = self.env['hr.payslip']
        hr_payslip_run_obj = self.env['hr.payslip.run']
        hr_payroll_register_obj = self.env['hr.payroll.register']

        register_id = self._context.get('active_id', False)
        if not register_id:
            raise Warning(_('Programming Error ! '
                            'Unable to determine Payroll Register Id.'))

        if not self.department_ids:
            raise Warning(_('Warning ! '
                            'No departments selected for payslip generation.'))
        register_rec = hr_payroll_register_obj.browse(register_id)
        # DateTime in db is store as naive UTC.
        # Convert it to explicit UTC and then convert that into
        # the our time zone.

        user_rec = self.env['res.users'].browse(self._uid)
        if not user_rec.tz:
            raise Warning(_('Warning ! '
                            'Please set Local Time Zone on User %s.') % (
                user_rec.name))
        local_tz = timezone(user_rec.tz)
        utc_tz = timezone('UTC')
        utcDTStart = utc_tz.localize(
            datetime.strptime(register_rec.date_start,
                              OEDATETIME_FORMAT))
        loclDTStart = utcDTStart.astimezone(local_tz)
        date_start = loclDTStart.strftime(OEDATE_FORMAT)
        utcDTEnd = utc_tz.localize(
            datetime.strptime(register_rec.date_end,
                              OEDATETIME_FORMAT))
        loclDTEnd = utcDTEnd.astimezone(local_tz)
        date_end = loclDTEnd.strftime(OEDATE_FORMAT)
        for department_rec in self.department_ids:
            run_res = {
                'name': department_rec.name,
                'date_start': register_rec.date_start,
                'date_end': register_rec.date_end,
                'register_id': register_id,
            }
            run_id = hr_payslip_run_obj.create(run_res)

            for hr_employee_rec in \
                    hr_employee_obj.search([
                        ('department_id', '=', department_rec.id)]):
                slip_data = hr_payslip_obj.onchange_employee_id(
                    date_start, date_end, hr_employee_rec.id)
                slip_vals = {
                    'employee_id': hr_employee_rec.id,
                    'name': slip_data['value'].get('name', False),
                    'struct_id':
                        slip_data['value'].get('struct_id', False),
                    'contract_id':
                        slip_data['value'].get('contract_id', False),
                    'payslip_run_id': run_id.id,
                    'input_line_ids': [
                        (0, 0, x) for x in slip_data['value'].get(
                            'input_line_ids', False)
                    ],
                    'worked_days_line_ids': [
                        (0, 0, x) for x in slip_data['value'].get(
                            'worked_days_line_ids', False)
                    ],
                    'date_from': register_rec.date_start,
                    'date_to': register_rec.date_end,
                }
                hr_payslip_rec = hr_payslip_obj.create(slip_vals)
                hr_payslip_rec.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
