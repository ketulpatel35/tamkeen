from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        if employee and employee.contract_id:
            return [employee.contract_id.id]
        else:
            clause_1 = ['&', ('date_end', '<=', date_to),
                        ('date_end', '>=', date_from)]
            # OR if it starts between the given dates
            clause_2 = ['&', ('date_start', '<=', date_to),
                        ('date_start', '>=', date_from)]
            # OR if it starts before the date_from and finish after the date_end (or never finish)
            clause_3 = ['&', ('date_start', '<=', date_from), '|',
                        ('date_end', '=', False), ('date_end', '>=', date_to)]
            clause_final = [('employee_id', '=', employee.id), '|',
                            '|'] + clause_1 + clause_2 + clause_3
            return self.env['hr.contract'].search(clause_final).ids

    def _get_days_before_joining(self, contract_rec):
        joining_date = False
        if contract_rec:
            joining_date = contract_rec.employee_id.initial_employment_date
        return joining_date

    def _get_overtime_hours(self, time_recording_line_rec, uom_hour, uom_day):
        total_overtime_leave_hours, total_unpaid_leave_hours = 0.0, 0.0
        number_of_days_overtime, number_of_days_unpaid = 0, 0
        for line in time_recording_line_rec:
            total_overtime_leave_hours += line.overtime_hours
            total_unpaid_leave_hours += line.unpaid_leave_hours
        if total_overtime_leave_hours:
            number_of_days_overtime = uom_hour._compute_quantity(total_overtime_leave_hours,
                                                        uom_day) \
                if uom_day and uom_hour else total_overtime_leave_hours / 8.0
        if total_unpaid_leave_hours:
            number_of_days_unpaid = uom_hour._compute_quantity(total_unpaid_leave_hours, uom_day) \
                if uom_day and uom_hour \
                else total_unpaid_leave_hours / 8.0
        return total_overtime_leave_hours, number_of_days_overtime, \
               total_unpaid_leave_hours, number_of_days_unpaid

    def _get_previous_payroll_period(self, date_from):
        date_from = datetime.strptime(date_from, OE_DATEFORMAT)
        previous_date_from = date_from - relativedelta(month=1)
        previous_date_to = date_from - relativedelta(days=1)
        # start_date = str(previous_date_from) + ' 00:00:00'
        # end_date = previous_date_to + relativedelta(hour=23, minute=59,
        #                                                  second=59)
        end_dt = previous_date_to.replace(hour=23, minute=59, second=59)
        previous_payroll_period = \
            self.env['hr.payroll.period'].search([
                ('date_start', '>=', str(previous_date_from)),
                ('date_end', '<=', str(end_dt))], limit=1)
        return previous_payroll_period

    def _get_worked_hours(self, contract_id, date_from, date_to):
        contract_rec = self.env['hr.contract'].browse(contract_id)
        time_recording_line_obj = self.env['sheet.time.recording.line']
        uom_hour = contract_rec.employee_id.resource_id.calendar_id.uom_id or \
                   self.env.ref('product.product_uom_hour',
                                raise_if_not_found=False)
        uom_day = self.env.ref('product.product_uom_day',
                               raise_if_not_found=False)
        number_of_hours = 0.0
        number_of_days = 0
        total_days, total_hours = 30, 240
        vals = {}
        time_recording_line_rec = time_recording_line_obj.search([(
            'payroll_locked_date', '>=', date_from),
            ('payroll_locked_date', '<=', date_to),
            ('payroll_locked', '=', True),
            ('employee_id', '=', contract_rec.employee_id.id)])
        previous_payroll_period = \
            self._get_previous_payroll_period(date_from)
        last_payroll_run_date = date_from
        if previous_payroll_period:
            last_payroll_run_date = previous_payroll_period.last_payroll_run_date
        overtime_unpaid_line_rec = time_recording_line_obj.search([(
            'payroll_locked_date', '>=', last_payroll_run_date),
            ('payroll_locked_date', '<=', date_to),
            ('payroll_locked', '=', True),
            ('employee_id', '=', contract_rec.employee_id.id)])
        overtime_hours, overtime_days, \
        total_unpaid_leave_hours, number_of_days_unpaid = \
            self._get_overtime_hours(overtime_unpaid_line_rec,
                                     uom_hour, uom_day)
        employee_joining_date = self._get_days_before_joining(contract_rec)
        for line in time_recording_line_rec:
            number_of_hours += line.total_paid_hours
            # total_unpaid_leave_hours += line.unpaid_leave_hours
        if number_of_hours:
            number_of_days = uom_hour._compute_quantity(number_of_hours, uom_day) \
                if uom_day and uom_hour \
                else number_of_hours / 8.0
        # if total_unpaid_leave_hours:
        #     number_of_days_unpaid = uom_hour._compute_quantity(total_unpaid_leave_hours, uom_day) \
        #         if uom_day and uom_hour \
        #         else total_unpaid_leave_hours / 8.0
        payslip_amendment_rec = self._get_payslip_amendment_with_number_of_hours(
            contract_rec)
        for amendment in payslip_amendment_rec:
            if amendment.corresponding_rule == 'unpaid':
                number_of_days_unpaid += amendment.number_of_days
        vals.update({
            'number_of_days': round(number_of_days),
            'number_of_hours': number_of_hours,
            'number_of_days_unpaid': round(number_of_days_unpaid),
            'total_unpaid_leave_hours': total_unpaid_leave_hours,
            'overtime_hours': overtime_hours,
            'overtime_days': round(overtime_days),
            'simulated_hours': total_hours - number_of_hours,
            'simulated_days': round(total_days - number_of_days),
            'employee_joining_date': employee_joining_date
        })
        return vals

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        # new_res = []
        remove_dict_sequence = [5]
        res = super(HrPayslip, self).get_worked_day_lines(contract_ids,
                                                          date_from, date_to)
        res = [line for line in res if line.get('sequence') not in
               remove_dict_sequence]
        if contract_ids:
            contract_id = contract_ids[0] or False
            total_days_to_pay_vals = {
                'name': _("Total Days to Pay"),
                'sequence': 2,
                'code': 'TDTP',
                'contract_id': contract_id,
            }
            res.append(total_days_to_pay_vals)
            total_simulated_days_vals = {
                'name': _("Total Simulated Days"),
                'sequence': 3,
                'code': 'TSD',
                'contract_id': contract_id,
            }
            res.append(total_simulated_days_vals)
            days_before_joining_vals = {
                'name': _("Days Before Joining"),
                'sequence': 4,
                'code': 'DBJ',
                'contract_id': contract_id,
            }
            res.append(days_before_joining_vals)
            unpaid_leave_vals = {
                'name': _("Unpaid Leave"),
                'sequence': 6,
                'code': 'UNP',
                'contract_id': contract_id,
            }
            res.append(unpaid_leave_vals)
            overtime_vals = {
                'name': _("Overtime"),
                'sequence': 7,
                'code': 'OT',
                'contract_id': contract_id,
            }
            res.append(overtime_vals)
            vals = self._get_worked_hours(contract_id, date_from, date_to)
            for line in res:
                if line.get('code') == 'WORK100':
                    line.update({'name': 'Total Recorded Days',
                                 'number_of_days': vals.get(
                                     'number_of_days'),
                                 'number_of_hours':
                                     vals.get('number_of_hours')})
                    # new_res.append(line)
                if line.get('code') == 'UNP':
                    line.update({
                        'number_of_days': vals.get(
                            'number_of_days_unpaid'),
                        'number_of_hours':
                            vals.get('total_unpaid_leave_hours')})

                if line.get('code') == 'OT':
                    line.update({'number_of_days':
                                     vals.get('overtime_days'),
                                 'number_of_hours':
                                     vals.get('overtime_hours')})
                if line.get('code') == 'TDTP':
                    line.update({'number_of_hours':
                                     vals.get('number_of_hours') +
                                     vals.get('simulated_hours'),
                                 'number_of_days':
                                     vals.get('number_of_days') +
                                     vals.get('simulated_days')})
                if line.get('code') == 'TSD':
                    line.update({'number_of_days':
                                     vals.get('simulated_days'),
                                 'number_of_hours':
                                     vals.get('simulated_hours')})
                if line.get('code') == 'DBJ' and vals.get(
                        'employee_joining_date') and vals.get(
                        'employee_joining_date') > date_from and vals.get(
                        'employee_joining_date') < date_to:
                    joining_date_strp = \
                        datetime.strptime(vals.get('employee_joining_date'),
                                          OE_DATEFORMAT) - relativedelta(
                            days=1)
                    days_after_joining_days = ((vals.get('number_of_days') +
                                           vals.get('simulated_days')) -
                                               int(joining_date_strp.day))

                    days_before_joining_days = ((vals.get('number_of_days') +
                                           vals.get('simulated_days')) -
                                                days_after_joining_days)
                    line.update({'number_of_days':
                                     days_before_joining_days,
                                 })
        return res

    def _get_payslip_amendment_with_number_of_hours(self, contract_rec):
        payslip_amendment_rec = self.env['hr.payslip.amendment']
        context = dict(self._context)
        payroll_period_rec = self.payroll_period_id
        if context.get('active_model') and context.get('active_model') == \
                'hr.payslip.run':
            payroll_period_rec = self.env['hr.payslip.run'].browse(
                context.get('active_id')).payroll_period_id
        if contract_rec and payroll_period_rec:
            # contract_rec = self.env['hr.contract'].browse(contract_id)
            payslip_amendment_rec = payslip_amendment_rec.search([
                ('state', '=', 'validate'),
                ('pay_period_id', '=', payroll_period_rec.id),
                ('employee_id', '=', contract_rec.employee_id.id),
                ('calculation_based_on', '=', 'days')])
        return payslip_amendment_rec

    def _get_payslip_amendment(self, contract_id):
        payslip_amendment_rec = self.env['hr.payslip.amendment']
        context = dict(self._context)
        payroll_period_rec = self.payroll_period_id
        if context.get('active_model') and context.get('active_model') == \
                'hr.payslip.run':
            payroll_period_rec = self.env['hr.payslip.run'].browse(
                context.get('active_id')).payroll_period_id
        if contract_id and payroll_period_rec:
            contract_rec = self.env['hr.contract'].browse(contract_id)
            payslip_amendment_rec = payslip_amendment_rec.search([
                ('state', '=', 'validate'),
                ('pay_period_id', '=', payroll_period_rec.id),
                ('employee_id', '=', contract_rec.employee_id.id),
                ('calculation_based_on', '=', 'amount')])
        return payslip_amendment_rec

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self). \
            get_inputs(contract_ids, date_from, date_to)
        if contract_ids:
            contract_id = contract_ids[0] or False
            payslip_amendment_rec = self._get_payslip_amendment(
                contract_id)
            if payslip_amendment_rec:
                for input in payslip_amendment_rec:
                    input_data = {
                        'name': input.name,
                        'code': input.code,
                        'contract_id': contract_id,
                        'amount': input.amount
                    }
                    res += [input_data]
        return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    payroll_period_id = fields.Many2one('hr.payroll.period',
                                        string='Payroll Period')

    @api.model
    def default_get(self, default_fields):
        res = super(HrPayslipRun, self).default_get(default_fields)
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

    @api.onchange('payroll_period_id')
    def onchange_payroll_period(self):
        self.date_start = False
        self.date_end = False
        if self.payroll_period_id:
            date_from = self.payroll_period_id.date_start
            date_to = self.payroll_period_id.date_end
            self.date_start = datetime.strptime(date_from,
                                                OE_DTFORMAT).date()
            self.date_end = datetime.strptime(date_to, OE_DTFORMAT).date()

    @api.multi
    def action_view_time_record(self):
        # time_record_wizard_tree = self.env.ref(
        #     'org_time_recording_payroll.sheet_time_record_line_tree_view')
        context = dict(self._context)
        domain = [('payroll_locked', '=', False),
                  ('payroll_locked_date', '=', False),
                  ('state', 'in', ('draft', 'simulated',
                                   'new_joiner', 'on_hold'))]
        context.update({'search_default_groupby_name': 1,
                        'search_default_groupby_employee_id': 1})
        return {
            'name': _('Time Recording'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree, form',
            'res_model': 'sheet.time.recording.line',
            # 'views': [(time_record_wizard_tree.id, 'tree')],
            'domain': domain,
            'context': context
        }

    @api.multi
    def generate_pyaslip_amendment(self):
        # amendment_tree_view = self.env.ref(
        #     'hr_payslip_amendment.view_payslip_amendment_tree')
        domain = []
        if self.payroll_period_id:
            domain.append(('pay_period_id', '=',
                           self.payroll_period_id.id))
        return {
            'name': _('Generate Payslip Amendment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'hr.payslip.amendment',
            'domain': domain
            # 'views': [(amendment_tree_view.id, 'tree')],
        }