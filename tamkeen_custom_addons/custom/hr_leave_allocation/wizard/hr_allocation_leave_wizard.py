# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import timedelta
from odoo.exceptions import Warning
from days360 import get_date_diff_days360
from datetime import date


class HrAllocationEmployees(models.TransientModel):
    _name = 'hr.allocation.employees'
    _description = 'Generate Allocation Request for all selected employees'

    employee_ids = fields.Many2many('hr.employee',
                                    'hr_allocation_employee_group_rel',
                                    'leave_allocation_id', 'employee_id',
                                    'Employees')
    active_batch_id = fields.Many2one('hr.leave.allocation.batch',
                                      string='Active Batch')

    @api.model
    def default_get(self, fields_list):
        res = super(HrAllocationEmployees, self).default_get(fields_list)
        if self._context and self._context.get('active_id'):
            res.update({'active_batch_id': self._context.get('active_id')})
        return res

    def get_employee_name(self, employee):
        name = '- ' + str(employee.name)
        if employee.f_employee_no:
            name += ' (' + str(
                employee.f_employee_no) + ')' + '\n'
        else:
            name += '\n'
        return name

    def _check_existing_employee(self, allocation_batch_rec):
        employee_list, employee_name = [], ''
        for line in allocation_batch_rec.holidays_ids:
            employee_list.append(line.employee_id.id)
        for employee in self.employee_ids:
            if employee.id in employee_list:
                name = self.get_employee_name(employee)
                employee_name += name
        if employee_name:
            raise Warning(_('You are not allowed to create a duplicate '
                            'record for that employees: %s') % employee_name)

    def _check_employee_contract(self, employee, warning_contract):
        if employee and not employee.contract_id:
            name = self.get_employee_name(employee)
            warning_contract += name
        return warning_contract

        # def _check_employee_contract_policy(self, employee, allocation_batch_rec,
        #                                     warning_accrual_policy):
        #     accrual_policy = False
        #     name = self.get_employee_name(employee)
        #     if employee and employee.contract_id and \
        #             not employee.contract_id.policy_group_id:
        #         warning_accrual_policy += name
        #     if employee and employee.contract_id and \
        #             employee.contract_id.policy_group_id:
        #         accrual_policy = self.env['hr.holidays'].\
        #             _get_employee_accural_policy(employee,
        #                                          allocation_batch_rec.leave_type_id)
        #         if not accrual_policy:
        #             warning_accrual_policy += name
        #     return warning_accrual_policy, accrual_policy

    def _check_employee_maximum_balance(self, employee,
                                        allocation_batch_rec,
                                        warning_max_balance):
        maximum_accumulative_balance = 0.0
        if employee.job_id:
            maximum_accumulative_balance = \
                employee.job_id.maximum_accumulative_balance
        vals_emp_leave_balance = self.env['hr.holidays']._get_employee_balance(
            allocation_batch_rec.leave_type_id, employee)
        emp_leave_balance = vals_emp_leave_balance.get('current_employee_balance')
        if (emp_leave_balance + allocation_batch_rec.allocation_days) >= \
                maximum_accumulative_balance:
            name = self.get_employee_name(employee)
            warning_max_balance += name
        return warning_max_balance

    def _check_for_new_joiner(self, employee, allocation_batch_rec,
                              warning_service_days,
                              warning_feature_hiring_date):
        # We check the employee service days
        minimum_employed_days = 0.0
        # if employee.job_id:
        #     minimum_employed_days = employee.job_id.trial_period
        srvc_months, dHire = \
            employee.get_months_service_to_date()[
                employee.id]
        name = self.get_employee_name(employee)
        if not dHire:
            warning_service_days += name
            return warning_service_days, warning_feature_hiring_date, False,\
                   False
        if str(dHire) >= allocation_batch_rec.date_end:
            warning_feature_hiring_date += name
        if str(dHire) >= allocation_batch_rec.date_start \
                and \
                        str(dHire) <= allocation_batch_rec.date_end:
            date_from = dHire
        else:
            date_from = fields.Date.from_string(
                allocation_batch_rec.date_start)
        date_to = fields.Date.from_string(
            allocation_batch_rec.date_end)
        employed_days = 0
        dCount = dHire
        if str(dHire) >= allocation_batch_rec.date_start \
                and \
                        str(
                            dHire) <= allocation_batch_rec.date_end:
            while dCount < date.today():
                employed_days += 1
                dCount += timedelta(days=+1)
        else:
            while dCount < date_from:
                employed_days += 1
                dCount += timedelta(days=+1)
        # if minimum_employed_days > employed_days:
        #     warning_service_days += name
        return warning_service_days, warning_feature_hiring_date, date_from,\
               date_to

    def _get_allocation_data(self, allocation_batch_rec, employee, accrual_bal):
        context = dict(self._context)
        leave_allocation = {
            'type': 'add',
            'employee_id': employee.id,
            'holiday_status_id':
                allocation_batch_rec.leave_type_id.id,
            'leave_allocation_batch_id': allocation_batch_rec.id
        }
        if context.get('type') == 'manual':
            leave_allocation.update({
                'name': 'Manual Leave Allocation (%.2f)' %
                        allocation_batch_rec.allocation_days,
                'number_of_days_temp':
                    allocation_batch_rec.allocation_days,
                'allocation_type': 'addition',
            })
        elif context.get('type') == 'accrual':
            leave_allocation.update({
                'name': 'Accrual Leave Allocation (%.2f)' %
                        accrual_bal,
                'number_of_days_temp': accrual_bal,
                'from_accrual': True,
                'allocation_date':
                    allocation_batch_rec.date_end,
                'allocation_type': 'addition',
            })
        elif context.get('type') == 'adjustment':
            leave_allocation.update({
                'name': 'Adjustment Leave Allocation (%.2f)' %
                        allocation_batch_rec.allocation_days,
                'number_of_days_temp': allocation_batch_rec.allocation_days,
                'allocation_type': 'deduction',
            })
        return leave_allocation

    def _check_employee_unpaid(self, allocation_batch_rec):
        minimum_allowed_unpaid_days, employee_name = 0.0, ''
        if allocation_batch_rec.company_id and \
                allocation_batch_rec.company_id.minimum_allowed_unpaid_days:
            minimum_allowed_unpaid_days = allocation_batch_rec.company_id.minimum_allowed_unpaid_days
        for employee in self.employee_ids:
            holiday_rec = self.env['hr.holidays'].search([('employee_id', '=', employee.id),
                                           ('holiday_status_id.code', '=',
                                            'UNP'), ('real_days', '>',
                                                     minimum_allowed_unpaid_days), ('type', '!=', 'add')])
            if holiday_rec:
                for holiday in holiday_rec:
                    if not((holiday.date_to < allocation_batch_rec.date_start \
                            or \
                            holiday.date_from >
                                        allocation_batch_rec.date_end)):
                        name = self.get_employee_name(employee)
                        employee_name += name
        if employee_name:
            raise Warning(_('Based on the minimum allowed unpaid days '
                            'policy, the following employee/s '
                            'are exceeding unpaid days'
                            'policy. %s')%employee_name)
        return True

    @api.multi
    def compute_sheet(self):
        context = self._context
        warning_contract, main_warning = '', ''
        warning_max_balance, warning_service_days, \
        warning_feature_hiring_date = '', '', ''
        employee_dict_list = []

        allocation_batch_obj = self.env['hr.leave.allocation.batch']
        if context and context.get('active_id'):
            allocation_batch_rec = allocation_batch_obj.browse(context.get(
                'active_id'))
            self._check_existing_employee(allocation_batch_rec)
            if not self.employee_ids:
                raise Warning(_('You need to add employees.'))
            self._check_employee_unpaid(allocation_batch_rec)
            for employee in self.employee_ids:
                warning_contract = self._check_employee_contract(employee,
                                                                 warning_contract)
                # warning_accrual_policy, accrual_policy = \
                #     self._check_employee_contract_policy(employee,
                #                                          allocation_batch_rec,
                #                                          warning_accrual_policy)
                if allocation_batch_rec.allocation_type == 'manual':
                    warning_max_balance = \
                        self._check_employee_maximum_balance(employee,
                                                             allocation_batch_rec,
                                                             warning_max_balance)
                    employee_data = \
                        self.with_context({'type': allocation_batch_rec.allocation_type}).\
                            _get_allocation_data(allocation_batch_rec,
                                                 employee, 0.0)
                    employee_dict_list.append(employee_data)
                elif allocation_batch_rec.allocation_type == 'adjustment':
                    employee_data = \
                        self.with_context(
                            {'type': allocation_batch_rec.allocation_type}). \
                            _get_allocation_data(allocation_batch_rec,
                                                 employee, 0.0)
                    employee_dict_list.append(employee_data)
                elif allocation_batch_rec.allocation_type == 'accrual':
                    warning_max_balance = \
                        self._check_employee_maximum_balance(employee,
                                                             allocation_batch_rec,
                                                             warning_max_balance)
                    warning_service_days, warning_feature_hiring_date, \
                    date_from, date_to = self._check_for_new_joiner(
                        employee, allocation_batch_rec,
                        warning_service_days, warning_feature_hiring_date)
                    daily_accrual_rate = self.env[
                        'hr.holidays']._get_employee_daily_balance(employee
                                                                   )
                    # daily_accrual_rate = self.env['hr.holidays']. \
                    #     _get_employee_daily_accrual_date(employee,
                    #                                      allocation_batch_rec.leave_type_id)
                    if date_from and date_to:
                        date_diff = \
                            get_date_diff_days360(date_from,
                                                  date_to) or 0.0
                        accrual_bal = round(date_diff *
                                            daily_accrual_rate)
                        employee_data = self.with_context(
                            {'type': allocation_batch_rec.allocation_type}). \
                            _get_allocation_data(allocation_batch_rec, employee, accrual_bal)
                        employee_dict_list.append(employee_data)
            if warning_contract:
                main_warning += 'The following employees have some ' \
                                'problems in allocating the balance' \
                                ', Kindly check their related Contracts:' \
                                '\n %s' % warning_contract
            # if warning_accrual_policy:
            #     main_warning += 'The following employees have some ' \
            #                     'problems in allocating the balance' \
            #                     ', Kindly check their related policies and ' \
            #                     'accrual configuration:' \
            #                     '\n %s' % warning_accrual_policy
            if warning_max_balance:
                main_warning += "The following employee is not eligible " \
                                "for the " \
                                "allocation because his/her balance will " \
                                "be greater than the allowed " \
                                "maximum balance.\n Kindly check below " \
                                "employess:\n %s" % warning_max_balance
            if warning_service_days:
                main_warning += 'The following employees have some ' \
                                'problems in allocating the balance' \
                                ', Kindly check their joining days:' \
                                '\n %s' % warning_service_days
            if warning_feature_hiring_date:
                main_warning += 'The following employees have some ' \
                                'problems in allocating the balance' \
                                ', Kindly check their joining days in ' \
                                'feature:' \
                                '\n %s' % warning_service_days
            if main_warning:
                raise Warning(_(main_warning))
            else:
                for line in employee_dict_list:
                    self.env['hr.holidays'].create(line)