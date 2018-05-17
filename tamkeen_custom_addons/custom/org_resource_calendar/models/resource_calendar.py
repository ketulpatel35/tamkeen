from odoo import models, api, fields, _
from datetime import datetime, timedelta


class WeekDays(models.Model):
    _name = 'hr.schedule.weekday'
    _description = 'Days of the Week'

    name = fields.Char(string='Name')
    sequence = fields.Integer(string='Sequence')


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    restday_ids = fields.Many2many(
        'hr.schedule.weekday',
        'resource_calendar_restdays_rel',
        'res_calendar_id',
        'weekday_id',
        string='Rest Days')
    public_holiday_ids = fields.Many2many('hr.holidays.public',
                                          'resource_calendar_public_holidays_rel',
                                          'res_calendar_id',
                                          'public_holiday_id',
                                          string='Public Holidays')
    default_scheduled_hours = fields.Float(string='Default Scheduled Hours')
    overnight_shift = fields.Boolean(string='Overnight Shift')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')

    @api.multi
    def get_rest_days(self):
        '''If the rest day(s) have been explicitly specified that's what is
        returned, otherwise a guess is returned based on the week days that
        are not scheduled. If an explicit rest day(s) has not been specified
        an empty list is returned. If it is able to figure out the rest days
        it will return a list of week day integers with Monday being 0.'''

        res = []
        for rec in self:
            if rec.restday_ids:
                res = [rd.sequence for rd in rec.restday_ids]
            else:
                weekdays = ['0', '1', '2', '3', '4', '5', '6']
                scheddays = []
                scheddays = [
                    wt.dayofweek for wt in rec.attendance_ids
                    if wt.dayofweek not in scheddays]
                print '$$', scheddays
                res = [int(d) for d in weekdays if d not in scheddays]
                # If there are no work days return nothing instead of *ALL* the
                # days in the week
                if len(res) == 7:
                    res = []
        return res

    @api.one
    def get_hours_by_weekday(self, day_no):
        ''' Return the number working hours in the template for day_no.
        For day_no 0 is Monday.'''
        delta = timedelta(seconds=0)
        for worktime in self.attendance_ids:
            if int(worktime.dayofweek) != day_no:
                continue
            fromHour, fromSep, fromMin = str(worktime.hour_from).partition('.')
            toHour, toSep, toMin = str(worktime.hour_to).partition('.')
            if len(fromSep) == 0 or len(toSep) == 0:
                raise Warning(_('Format of working hours is incorrect'))

            delta += datetime.strptime(toHour + ':' + toMin, '%H:%M') - \
                     datetime.strptime(fromHour + ':' + fromMin, '%H:%M')
        return float(delta.seconds / 60) / 60.0


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'
    _order = 'sequence'

    scheduled_hours = fields.Float(string='Scheduled Hours')
    flexible_hours = fields.Float(string='Flexible Hours')
    late_time = fields.Float(string='Late Time(M)')
    leave_early_time = fields.Float(string='Leave Early Time(M)')
    beginning_in = fields.Float(string='Beginning In')
    beginning_out = fields.Float(string='Beginning Out')
    ending_in = fields.Float(string='Ending In')
    ending_out = fields.Float(string='Ending Out')
    sequence = fields.Integer(sring='Sequence')

    @api.model
    def default_get(self, fields_list):
        res = super(ResourceCalendarAttendance, self).default_get(fields_list)
        context = dict(self._context)
        if context and context.get('default_scheduled_hours'):
            if context.get('default_scheduled_hours'):
                res.update({'scheduled_hours':
                                context.get('default_scheduled_hours')})
        return res