# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from dateutil.relativedelta import relativedelta


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def _check_employee_start_date(self):
        # check employee contract start date
        new_employee = False

        for payslip in self:
            date_list = []
            new_employee = False
            for contract in self.env['hr.contract'].search(
                    [('employee_id', '=', payslip.employee_id.id)]):
                date_list.append(contract.date_start)
            if date_list:
                smallest_date = min(date_list)

                if smallest_date > payslip.date_from:
                    new_employee = True

                payslip.check_employee_start_date = new_employee

    @api.multi
    def _first_contract_date(self):
        # from many contract search for minimum contract date
        res = {}
        for payslip in self:
            date_list = []
            for contract in self.env['hr.contract'].search(
                    [('employee_id', '=', payslip.employee_id.id)]):
                date_list.append(contract.date_start)
            if date_list:
                smallest_date = min(date_list)
                payslip.first_contract_date = smallest_date
                return res
        return False

    def _check_hiring_date(self, date_from, date_to, employee_rec,
                           number_of_days):
        date_from = datetime.strptime(date_from, OE_DFORMAT).date()
        date_to = datetime.strptime(date_to, OE_DFORMAT).date()
        previous_date_from = date_from - relativedelta(month=1)
        previous_date_to = date_from - relativedelta(days=1)
        previous_month_days = int((previous_date_to -
                                   previous_date_from).days) + 1
        if employee_rec.user_id and employee_rec.user_id.company_id:
            current_employee_lock_day = \
                employee_rec.user_id.company_id.payroll_lock_day
            current_lock_date = datetime.today().date() + \
                                relativedelta(
                                    day=int(current_employee_lock_day))
            previous_month_current_lock_date = \
                current_lock_date - relativedelta(month=1)
            if employee_rec.initial_employment_date:
                hiring_date = datetime.strptime(
                    employee_rec.initial_employment_date, OE_DFORMAT).date()
                hiring_day = int(hiring_date.day)
                if hiring_date >= date_from and hiring_date <= date_to and \
                                hiring_date < current_lock_date:
                    number_of_days = int(number_of_days - hiring_day)
                elif hiring_date >= previous_date_from and hiring_date <= \
                        previous_date_to and hiring_date > \
                        previous_month_current_lock_date:
                    remaining_days = int(previous_month_days - hiring_day) + 1
                    number_of_days += remaining_days
        return number_of_days


    @api.multi
    def _number_of_days_new_employee(self):
        # count number of days
        for payslip in self:
            employee_rec = payslip.employee_id
            date_start = payslip.date_from
            date_to = payslip.date_to
            date_list = []
            for contract in self.env['hr.contract'].search(
                    [('employee_id', '=', payslip.employee_id.id)]):
                date_list.append(contract.date_start)
            if date_list:
                smallest_date = min(date_list)
                delta_30 = \
                    datetime.strptime(date_to, OE_DFORMAT) - \
                    datetime.strptime(date_start, OE_DFORMAT)
                delta_30_days = delta_30.days + 1
                delta_30_days = 30 - delta_30_days
                if smallest_date > date_start:
                    delta = \
                        datetime.strptime(date_to, OE_DFORMAT) - \
                        datetime.strptime(smallest_date, OE_DFORMAT)
                    number_of_days = \
                        (delta.days and delta.days) + 1 + delta_30_days
                else:
                    delta = \
                        datetime.strptime(date_to, OE_DFORMAT) - \
                        datetime.strptime(date_start, OE_DFORMAT)
                    number_of_days = \
                        (delta.days and delta.days) + 1 + delta_30_days
                if number_of_days <= 0:
                    number_of_days = 1
                #calculating employee hiring date with lock date based on
                # company configuration.
                number_of_days = payslip._check_hiring_date(date_start,
                                                            date_to,
                                                            employee_rec, number_of_days)
                payslip.number_of_days_new_employee = number_of_days

    check_employee_start_date = fields.Boolean(
        compute='_check_employee_start_date', string='New Employee')
    first_contract_date = fields.Date(string='First Contract Date',
                                      compute='_first_contract_date')
    number_of_days_new_employee = fields.Float(
        string='New Employee Number Of days',
        compute='_number_of_days_new_employee')
