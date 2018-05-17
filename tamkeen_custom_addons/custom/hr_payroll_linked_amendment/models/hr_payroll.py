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

    def _get_above_30(self, date_from, date_to):
        date_from = datetime.strptime(date_from, OE_DATEFORMAT)
        date_to = datetime.strptime(date_to, OE_DATEFORMAT)
        diff_days = abs((date_to - date_from).days) + 1
        if diff_days == 30:
            return 0
        elif diff_days == 31:
            return 1

    def _get_worked_hours(self, contract_id, date_from, date_to):
        contract_rec = self.env['hr.contract'].browse(contract_id)
        # time_recording_line_obj = self.env['sheet.time.recording.line']
        uom_hour = contract_rec.employee_id.resource_id.calendar_id.uom_id or \
                   self.env.ref('product.product_uom_hour',
                                raise_if_not_found=False)
        uom_day = self.env.ref('product.product_uom_day',
                               raise_if_not_found=False)
        total_unpaid_leave_hours, total_hour_before_joining_days, \
        total_absence_hours = 0.0, 0.0, 0.0
        number_of_days_unpaid, days_before_joining_days, \
        number_of_days_absence = 0, 0, 0
        vals = {}
        above_30 = 0
        employee_joining_date = self._get_days_before_joining(contract_rec)
        if employee_joining_date > str(date_from) and employee_joining_date < \
                str(date_to):
            joining_date_strp = \
                datetime.strptime(employee_joining_date, OE_DATEFORMAT) - \
                relativedelta(days=1)
            days_after_joining_days = 30 - int(joining_date_strp.day)
            days_before_joining_days = 30 - days_after_joining_days
            above_30 = self._get_above_30(date_from, date_to)
        payslip_amendment_rec = self._get_payslip_amendment_with_number_of_hours(
            contract_rec)
        for amendment in payslip_amendment_rec:
            if amendment.corresponding_rule == 'unpaid' and \
                            amendment.calculation_based_on == 'days_hours':
                total_unpaid_leave_hours += amendment.amendment_hours
                number_of_days_unpaid += amendment.number_of_days
            if amendment.corresponding_rule == 'absence' and \
                            amendment.calculation_based_on == 'days_hours':
                total_absence_hours += amendment.amendment_hours
                number_of_days_absence += amendment.number_of_days

        if days_before_joining_days:
            total_hour_before_joining_days = uom_day._compute_quantity(
                days_before_joining_days, uom_hour) \
                if uom_day and uom_hour \
                else days_before_joining_days * 8.0
        vals.update({
            'number_of_days_unpaid': round(number_of_days_unpaid),
            'total_unpaid_leave_hours': total_unpaid_leave_hours,
            'days_before_joining_days': days_before_joining_days,
            'total_hour_before_joining_days': total_hour_before_joining_days,
            'total_absence_hours': total_absence_hours,
            'number_of_days_absence': number_of_days_absence,
            'above_30': above_30
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
            unpaid_leave_vals = {
                'name': _("Unpaid Leave"),
                'sequence': 4,
                'code': 'UNP',
                'contract_id': contract_id,
            }
            absence_vals = {
                'name': _("Absence"),
                'sequence': 3,
                'code': 'ABS',
                'contract_id': contract_id,
            }
            days_before_joining_vals = {
                'name': _("Days Before Joining"),
                'sequence': 6,
                'code': 'DBJ',
                'contract_id': contract_id,
            }
            above_30_vals = {
                'name': _("Above 30"),
                'sequence': 7,
                'code': 'ABV',
                'contract_id': contract_id,
            }
            res.append(unpaid_leave_vals)
            res.append(days_before_joining_vals)
            res.append(absence_vals)
            res.append(above_30_vals)
            vals = self._get_worked_hours(contract_id, date_from, date_to)
            for line in res:
                if line.get('code') == 'WORK100':
                    line.update({'name': 'Total Recorded Days'})
                if line.get('code') == 'UNP':
                    line.update({
                        'number_of_days': vals.get(
                            'number_of_days_unpaid'),
                        'number_of_hours':
                            vals.get('total_unpaid_leave_hours')})
                if line.get('code') == 'DBJ' and vals.get(
                        'days_before_joining_days'):
                    line.update({'number_of_days':
                        vals.get(
                            'days_before_joining_days'),
                        'number_of_hours': vals.get(
                            'total_hour_before_joining_days')
                                 })
                if line.get('code') == 'ABS' and vals.get(
                        'days_before_joining_days'):
                    line.update({'number_of_days':
                        vals.get(
                            'number_of_days_absence'),
                        'number_of_hours': vals.get(
                            'total_absence_hours')
                    })
                if line.get('code') == 'ABV' and vals.get(
                        'above_30'):
                    line.update({'number_of_days':
                        vals.get(
                            'above_30'),
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
                ('calculation_based_on', '=', 'days_hours')])
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