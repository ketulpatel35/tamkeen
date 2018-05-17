from odoo import models, api, fields, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATEFORMAT
from datetime import timedelta


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _get_schedule_template(self):
        schedule_template = False
        if self.employee_id and self.employee_id.contract_id and \
                self.employee_id.contract_id.working_hours:
            schedule_template \
                = self.employee_id.contract_id.working_hours
        return schedule_template

    def _get_rest_days(self, schedule_template):
        rest_days = []
        if schedule_template and self.holiday_status_id and \
                not self.holiday_status_id.ex_rest_days:
            rest_days = schedule_template.get_rest_days()
        return rest_days

    def _get_default_hours(self, schedule_template):
        default_scheduled_hours = 0.0
        if schedule_template and schedule_template.default_scheduled_hours:
            if ':' in schedule_template.default_scheduled_hours:
                default_scheduled_hours = \
                    schedule_template.default_scheduled_hours.replace(':', '.')
        return float(default_scheduled_hours)

    def _get_public_holidays(self, schedule_template):
        hhplo = self.env['hr.holidays.public.line']
        p_holidays_date = []
        # if schedule_template and self.holiday_status_id and not\
        #         self.holiday_status_id.ex_public_holidays:
        for public_holiday in schedule_template.public_holiday_ids:
            hhplo += public_holiday.get_holidays_list(public_holiday.year,
                                             self.employee_id.id)
            for line in hhplo:
                p_holidays_date.append(line.date)
        return p_holidays_date

    @api.depends('date_from', 'date_to')
    def _get_leaved_hours(self):
        total_time = 0.0
        if self.date_from and self.date_to:
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
            month_days = (date_to - date_from).days + 1
            schedule_template = self._get_schedule_template()
            rest_days = self._get_rest_days(schedule_template)
            default_hours = self._get_default_hours(schedule_template)
            public_holidays = self._get_public_holidays(schedule_template)
            if schedule_template:
                for index in range(0, month_days):
                    current = date_from + timedelta(index)
                    # for index in range(0, month_days):
                    weekDay = current.weekday()
                    if current.weekday() in rest_days:
                        total_time += default_hours
                    # elif str(current.date()) in public_holidays and not \
                    #         self.holiday_status_id.ex_public_holidays:
                    #     total_time += default_hours
                    elif self.holiday_status_id.ex_public_holidays and \
                            str(current.date()) in public_holidays:
                        total_time -= default_hours
                    for line in schedule_template.attendance_ids:
                        if int(weekDay) == int(line.dayofweek):
                            on_duty_time = line.hour_from
                            off_duty_time = line.hour_to
                            if ':' in str(off_duty_time):
                                off_duty_time = off_duty_time.replace(':', '.')
                            if ':' in on_duty_time:
                                on_duty_time = on_duty_time.replace(':', '.')
                            total_time += float(float(off_duty_time) -
                                                float(on_duty_time))
        self.leaved_hours = total_time

    leaved_hours = fields.Float(string='Leave Hours',
                                compute='_get_leaved_hours')