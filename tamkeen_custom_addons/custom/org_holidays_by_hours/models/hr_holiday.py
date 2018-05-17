from odoo import models, api, fields, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATEFORMAT
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class HrHolidaysMonthlyPartition(models.Model):
    _name = 'hr.holidays.monthly.partition'

    name = fields.Char(string='Month')
    hours = fields.Float(string='Hours')
    days = fields.Float(string='Days')
    holiday_id = fields.Many2one('hr.holidays', string='Holidays')
    payroll_period_id = fields.Many2one('hr.payroll.period',
                                        string='Payroll Period')
    amendment_created = fields.Boolean(string='amendment Created')


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _get_duty_time(self, line):
        on_duty_time = line.hour_from
        off_duty_time = line.hour_to
        off_hour, off_minute, on_hour, on_minute = 0, \
                                                   0, \
                                                   0, 0
        if '.' in str(off_duty_time):
            off_hour = int(str(off_duty_time).split(
                '.')[0])
            off_minute = int(str(off_duty_time).split(
                '.')[1])
        if '.' in str(on_duty_time):
            on_hour = int(str(on_duty_time).split(
                '.')[0])
            on_minute = int(str(on_duty_time).split(
                '.')[1])
        return on_hour, off_hour, on_minute, off_minute

    def _get_date_from_to(self):
        date_from_str = str(self.date_from).replace(
            str(self.date_from.split(
                ' ')[1]), '00:00:00')
        date_to_str = str(self.date_to).replace(
            str(self.date_from.split(
                ' ')[1]), '00:00:00')
        date_from = datetime.strptime(date_from_str,
                                      OE_DATEFORMAT)
        date_to = datetime.strptime(date_to_str,
                                    OE_DATEFORMAT)
        return date_from, date_to

    def _get_payroll_period(self, current, vals):
        payroll_period_obj = self.env['hr.payroll.period']
        print current, type(current)
        payroll_period_rec = payroll_period_obj.\
            search([('date_start', '<=', str(current)),
                    ('date_end', '>=', str(current))], limit=1)
        if payroll_period_rec:
            vals.update({'payroll_period_id': payroll_period_rec.id})
        return vals

    @api.depends('date_from', 'date_to')
    def _get_leaved_hours(self):
        total_time = 0.0
        total_days = 0
        leave_hours, days_of_leave = 0.0, 0
        monthly_partition_lst = []
        new_monthly_partition_lst = []
        if self.type == 'remove':
            if self.date_from and self.date_to:
                date_from, date_to = self._get_date_from_to()
                month_days = (date_to - date_from).days + 1
                schedule_template = self._get_shift_for_employee(self.employee_id)
                rest_days = self._get_rest_days(self.employee_id)
                default_hours = self._get_default_hours(schedule_template)
                public_holidays = self._get_public_holidays(schedule_template)
                if schedule_template:
                    for index in range(0, month_days):
                        current = date_from + timedelta(index)
                        weekDay = current.weekday()
                        if weekDay in rest_days and \
                                not self.holiday_status_id.ex_rest_days:
                            total_time += default_hours
                            total_days += (default_hours) / (default_hours)
                        elif self.holiday_status_id.ex_public_holidays and \
                                str(current.date()) in public_holidays:
                            total_time -= default_hours
                            total_days -= (default_hours) / (default_hours)
                        else:
                            for line in schedule_template.attendance_ids:
                                if int(weekDay) == int(line.dayofweek):
                                    on_hour, off_hour, on_minute, off_minute = \
                                        self._get_duty_time(line)
                                    start_date = current + relativedelta(
                                        hour=on_hour, minute=on_minute)
                                    end_date = current + relativedelta(
                                        hour=off_hour, minute=off_minute)
                                    difference = relativedelta(end_date, start_date)
                                    hour = float(str(difference.hours) + '.' + str(
                                        difference.minutes))
                                    total_time += hour
                                    total_days += (hour / line.scheduled_hours)
                        if not any(d['name'] == str(current.strftime('%b')) for
                                   d in monthly_partition_lst):
                            total_days = (hour / line.scheduled_hours)
                            total_time = hour
                            vals = {'name': str(current.strftime('%b')),
                                    'days': total_days, 'hours': total_time}
                            vals = self._get_payroll_period(
                                current, vals)
                            monthly_partition_lst.append(vals)
                        else:
                            existing_month_dict = next(d for i, d in enumerate(
                                monthly_partition_lst) if
                                 d.get('name') == str(current.strftime('%b'))
                                 )
                            existing_month_dict.update({
                                'days': total_days, 'hours': total_time
                            })
            for line in monthly_partition_lst:
                for key, value in line.items():
                    if key == 'hours':
                        leave_hours += value
                    elif key == 'days':
                        days_of_leave += value
                new_monthly_partition_lst.append((0, 0, line))
        self.monthly_partition_ids = new_monthly_partition_lst
        self.leaved_hours = leave_hours
        self.real_days = days_of_leave


    leaved_hours = fields.Float(string='Leave Hours',
                                compute='_get_leaved_hours', store=True)
    monthly_partition_ids = fields.One2many('hr.holidays.monthly.partition',
                                            'holiday_id', string='Monthly '
                                                                 'Partition',
                                            compute='_get_leaved_hours',
                                            store=True)
