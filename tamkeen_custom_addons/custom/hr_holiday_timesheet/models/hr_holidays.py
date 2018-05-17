# -*- coding: utf-8 -*-
# © 2017 Jerome Guerriat, Tobias Zehntner
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import _, api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class HRHolidays(models.Model):
    _inherit = 'hr.holidays'

    message = fields.Char('Selected days', compute='number_of_days_calculated')
    number_of_days_calculated = fields.Float(
        compute='number_of_days_calculated',
        inverse='set_number_of_days',
        store=True)

    # For leave allocation
    @api.multi
    def set_number_of_days(self):
        self.ensure_one()
        self.number_of_days_temp = self.number_of_days_calculated

    @api.multi
    @api.depends('date_from', 'date_to', 'employee_id')
    def number_of_days_calculated(self):
        for holiday in self:
            holiday.deduct_special_days()

    # Inherit function from module hr_holiday_exclude_special_days
    # Use multiple of half days and add message
    def deduct_special_days(self, number_of_days=0):
        if self.type == 'add':
            return

        message = ''
        leave_days = 0
        if self.date_from and self.date_to and self.employee_id:
            special_days = self.get_special_days(self.date_from, self.date_to,
                                                 self.employee_id)

            time_from = self.str_to_timezone(self.date_from)
            time_to = self.str_to_timezone(self.date_to)
            for timestamp in self.datespan(time_from, time_to):
                if timestamp.date() in special_days:
                    message = '%s<span>%s %s<br/></span>' % (
                        message, timestamp.date(),
                        special_days[timestamp.date()])
                else:
                    if self.is_full_day(timestamp, time_from, time_to):
                        leave_days += 1
                        message = '%s<span>%s <b>Full day</b><br/></span>' % (
                            message, timestamp.date())
                    else:
                        leave_days += 0.5
                        message = '%s<span>%s <b><i>Half day</i></b><br/></span>' % (
                            message, timestamp.date())

        self.message = message
        self.number_of_days_temp = leave_days
        return leave_days

    @api.multi
    @api.constrains('number_of_days')
    def _check_number_of_days(self):
        for holiday in self:
            if holiday.type == 'remove' \
                    and holiday.number_of_days \
                    and holiday.number_of_days % 0.5 != 0:
                raise exceptions.ValidationError(
                    _('Please select a multiple of 0.5 days'))

    @api.multi
    def action_validate(self):
        '''
        Method used to create timesheet lines when a holiday is approved
        :return:
        '''
        return_value = super(HRHolidays, self).action_validate()
        for holiday in self.filtered(lambda r: r.state == 'validate'):
            if not holiday.employee_id:
                continue

            if not holiday.employee_id.user_id:
                raise exceptions.ValidationError(_(
                    'You cannot validate a leave for an employee without '
                    'a user'))
            if holiday.number_of_days > 0:
                continue
            if not (holiday.date_from or holiday.date_to):
                continue

            employee = holiday.employee_id

            time_from = self.str_to_timezone(holiday.date_from)
            time_to = self.str_to_timezone(holiday.date_to)

            for timestamp in self.datespan(time_from, time_to):
                company = employee.company_id

                if not company:
                    raise exceptions.ValidationError(_(
                        'The selected employee has no company'))

                deduct_saturday = company.deduct_saturday_in_leave
                deduct_sunday = company.deduct_sunday_in_leave

                # Do not create timesheet lines for weekends
                if (deduct_saturday and timestamp.weekday() == 5) \
                        or (deduct_sunday and timestamp.weekday() == 6):
                    continue

                is_full_day = holiday.is_full_day(timestamp, time_from,
                                                  time_to)
                date = timestamp.date()
                hours = company.hours_per_day

                if hours <= 0:
                    raise exceptions.ValidationError(_(
                        'Please set your company normal working day'))

                if is_full_day:
                    self.create_leave_analytic_line(
                        holiday, employee, date, hours)
                else:
                    hours /= 2
                    self.create_leave_analytic_line(
                        holiday, employee, date, hours)

        return return_value

    def get_hours_per_day(self):
        """
        Inherit method from hr_holiday_excluce_special_days to use hours per
        day defined in this module when creating leaves
        """
        return self.env.user.company_id.hours_per_day

    @api.multi
    @api.constrains('state')
    def remove_lines(self):
        """
        Remove any analytic lines from leave in state draft, refuse, cancel
        """
        holidays = self.filtered(
            lambda h: h.state in ['draft', 'cancel', 'refuse'])
        lines = self.env['account.analytic.line'].sudo().search(
            [('leave_id', 'in', holidays.ids)])
        lines.sudo().unlink()

    def create_leave_analytic_line(self, holiday, employee, concerned_day,
                                   hours):

        account = self.env.ref('hr_holiday_timesheet.account_leave')
        project = self.env.ref('hr_holiday_timesheet.project_leave')

        return self.env['account.analytic.line'].sudo().create({
            'account_id': account.id,
            'project_id': project.id,
            'company_id': employee.company_id.id,
            'amount': 0,
            'date': concerned_day,
            'name': holiday.name,
            'amount_currency': 0,
            'is_timesheet': True,
            'unit_amount': hours,
            'user_id': employee.user_id.id,
            'leave_id': self.id
        })

    @api.model
    def create(self, vals):
        if vals['type'] == 'remove' and \
                self.env['hr_timesheet_sheet.sheet'].search([
                    ('date_from', '<', vals['date_to']),
                    ('date_to', '>', vals['date_from']),
                    ('employee_id', '=', vals['employee_id']),
                    ('state', '!=', 'draft')
                ]):
            raise Warning(_('You cannot book a holiday for a period for which'
                            ' you already have submitted your timesheet'))

        return super(HRHolidays, self).create(vals)

    @api.multi
    def is_full_day(self, timestamp, time_from, time_to):
        """
        Counts as full day if:
        - Holiday lasts one day and is longer than hours_per_day by half
        - Day is first day of the holiday and starts before 12pm
        - Day is last day of the holiday and ends after 12pm
        """
        self.ensure_one()
        date_from = time_from.date()
        date_to = time_to.date()
        date_concerned = timestamp.date()

        if date_concerned == date_from == date_to:
            # One day holiday
            hours = (time_to - time_from).total_seconds() / 60 / 60
            hours_per_day = self.env.user.company_id.hours_per_day
            return hours > (hours_per_day / 2)
        else:
            # Multi day holiday
            return (date_concerned == date_from
                    and time_from.time() < datetime.time(12, 0)) \
                   or (date_concerned == date_to
                       and time_to.time() > datetime.time(12, 0)) \
                   or (date_concerned != date_to
                       and date_concerned != date_from)

    def datespan(self, start_date, end_date, delta=datetime.timedelta(days=1)):
        current_date = start_date
        while current_date.date() <= end_date.date():
            yield current_date
            current_date += delta

    def str_to_timezone(self, time_string):
        time_obj = datetime.datetime.strptime(time_string, DTF)

        return fields.Datetime.context_timestamp(self.env.user,
                                                 time_obj)
