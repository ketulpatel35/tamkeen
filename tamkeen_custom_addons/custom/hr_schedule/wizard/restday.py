from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT

import logging

_l = logging.getLogger(__name__)


class restday(models.TransientModel):
    _name = 'hr.restday.wizard'
    _description = 'Schedule Template Change Wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr.contract',
                                  related='employee_id.contract_id',
                                  string='Contract')
    st_current_id = fields.Many2one('hr.schedule.template',
                                    'Current Template')
    st_new_id = fields.Many2one('hr.schedule.template', string='New Template')
    permanent = fields.Boolean(string='Make Permanent')
    temp_restday = fields.Boolean(
        'Temporary Rest Day Change',
        help="If selected, change "
             "the rest day to the "
             "specified day only "
             "for the selected "
             "schedule.")
    dayofweek = fields.Selection([('0', 'Monday'),
                                  ('1', 'Tuesday'),
                                  ('2', 'Wednesday'),
                                  ('3', 'Thursday'),
                                  ('4', 'Friday'),
                                  ('5', 'Saturday'),
                                  ('6', 'Sunday')], string='Rest Day')
    temp_week_start = fields.Date(string='Start of Week')
    week_start = fields.Date(string='Start of Week')

    @api.onchange('employee_id')
    def onchange_employee(self):
        for rec in self:
            if rec.employee_id:
                rec.st_current_id = rec.employee_id.contract_id. \
                    working_hours.id

    @api.model
    def _create_detail(self, schedule, actual_dayofweek, template_dayofweek,
                       week_start):

        # First, see if there's a schedule for the actual dayofweek.
        #  If so, use it.
        for worktime in schedule.template_id.worktime_ids:
            if worktime.dayofweek == actual_dayofweek:
                template_dayofweek = actual_dayofweek

        prevutcdtStart = False
        prevDayofWeek = False
        user = self.env['res.users'].browse(self._uid)
        local_tz = timezone(user.tz)
        dSchedStart = datetime.strptime(schedule.date_start, OE_DFORMAT).date()
        dWeekStart = schedule.date_start < week_start and datetime.strptime(
            week_start, OE_DFORMAT).date() or dSchedStart

        for worktime in schedule.template_id.worktime_ids:

            if worktime.dayofweek != template_dayofweek:
                continue

            hour, sep, minute = worktime.hour_from.partition(':')
            toHour, toSep, toMin = worktime.hour_to.partition(':')
            if len(sep) == 0 or len(toSep) == 0:
                raise ValidationError(_('Invalid Time Format The time should '
                                        'be entered as HH:MM'))

            # XXX - Someone affected by DST should fix this
            #
            dtStart = datetime.strptime(
                dWeekStart.strftime('%Y-%m-%d') +
                ' ' +
                hour +
                ':' +
                minute +
                ':00',
                '%Y-%m-%d %H:%M:%S')
            locldtStart = local_tz.localize(dtStart, is_dst=False)
            utcdtStart = locldtStart.astimezone(utc)
            if actual_dayofweek != '0':
                utcdtStart = utcdtStart + \
                    relativedelta(days=+int(actual_dayofweek))
            dDay = utcdtStart.astimezone(local_tz).date()

            # If this worktime is a continuation (i.e - after lunch) set
            # the start
            # time based on the difference from the previous record
            if prevDayofWeek and prevDayofWeek == actual_dayofweek:
                prevHour = prevutcdtStart.strftime('%H')
                prevMin = prevutcdtStart.strftime('%M')
                curHour = utcdtStart.strftime('%H')
                curMin = utcdtStart.strftime('%M')
                delta_seconds = (
                    datetime.strptime(
                        curHour +
                        ':' +
                        curMin,
                        '%H:%M') -
                    datetime.strptime(
                        prevHour +
                        ':' +
                        prevMin,
                        '%H:%M')).seconds
                utcdtStart = prevutcdtStart + \
                    timedelta(seconds=+delta_seconds)
                dDay = prevutcdtStart.astimezone(local_tz).date()

            delta_seconds = (
                datetime.strptime(
                    toHour +
                    ':' +
                    toMin,
                    '%H:%M') -
                datetime.strptime(
                    hour +
                    ':' +
                    minute,
                    '%H:%M')).seconds
            utcdtEnd = utcdtStart + timedelta(seconds=+delta_seconds)

            val = {
                'name': schedule.name,
                'dayofweek': actual_dayofweek,
                'day': dDay,
                'date_start': utcdtStart.strftime('%Y-%m-%d %H:%M:%S'),
                'date_end': utcdtEnd.strftime('%Y-%m-%d %H:%M:%S'),
                'schedule_id': schedule.id,
            }
            schedule.write({'detail_ids': [(0, 0, val)]})

            prevDayofWeek = worktime.dayofweek
            prevutcdtStart = utcdtStart

    @api.multi
    def _change_restday(self, employee_id, week_start, dayofweek):
        sched_obj = self.env['hr.schedule']
        sched_detail_obj = self.env['hr.schedule.detail']
        schedule_ids = sched_obj.search([
            ('employee_id', '=', employee_id),
            ('date_start', '<=', week_start),
            ('date_end', '>=', week_start),
            ('state', 'not in', ['locked'])])
        if schedule_ids.date_start:
            dtFirstDay = datetime.strptime(
                schedule_ids.date_start, OE_DTFORMAT)
            date_start = dtFirstDay.strftime(OE_DFORMAT) < week_start and \
                week_start + ' ' + dtFirstDay.strftime(
                '%H:%M:%S') or dtFirstDay.strftime(OE_DTFORMAT)
            dtNextWeek = datetime.strptime(
                date_start, OE_DTFORMAT) + relativedelta(weeks=+1)

            # First get the current rest days
            rest_days = sched_obj.get_rest_days_by_id(schedule_ids.id,
                                                      dtFirstDay.strftime(
                                                          OE_DFORMAT))

            # Next, remove the schedule detail for the new rest day
            for dtl in schedule_ids.detail_ids:
                if dtl.date_start < week_start or datetime.strptime(
                        dtl.date_start, OE_DTFORMAT) >= dtNextWeek:
                    continue
                if dtl.dayofweek == dayofweek:
                    sched_detail_obj.unlink(dtl.id)

                    # Enter the new rest day(s)
                    #
            sched_obj = self.env['hr.schedule']
            nrest_days = [dayofweek] + rest_days[1:]
            dSchedStart = datetime.strptime(schedule_ids.date_start,
                                            OE_DFORMAT).date()
            dWeekStart = schedule_ids.date_start < week_start and \
                datetime.strptime(week_start, OE_DFORMAT).date() or \
                dSchedStart
            if dWeekStart == dSchedStart:
                sched_obj.add_restdays(schedule_ids, 'restday_ids1',
                                       rest_days=nrest_days)
            elif dWeekStart == dSchedStart + relativedelta(days=+7):
                sched_obj.add_restdays(schedule_ids, 'restday_ids2',
                                       rest_days=nrest_days)
            elif dWeekStart == dSchedStart + relativedelta(days=+14):
                sched_obj.add_restdays(schedule_ids, 'restday_ids3',
                                       rest_days=nrest_days)
            elif dWeekStart == dSchedStart + relativedelta(days=+21):
                sched_obj.add_restdays(schedule_ids, 'restday_ids4',
                                       rest_days=nrest_days)
            elif dWeekStart == dSchedStart + relativedelta(days=+28):
                sched_obj.add_restdays(schedule_ids, 'restday_ids5',
                                       rest_days=nrest_days)

            # Last, add a schedule detail for the first rest day in
            # the week using the
            # template for the new (temp) rest day
            if len(rest_days) > 0:
                self._create_detail(schedule_ids, str(rest_days[0]), dayofweek,
                                    week_start)

    @api.multi
    def _remove_add_schedule(self, schedule_id, week_start, tpl_id):

        # Remove the current schedule and add a new one in its place
        # according to
        # the new template. If the week that the change starts in is not at the
        # beginning of a schedule create two new schedules to accomodate the
        # truncated old one and the partial new one.

        sched_obj = self.env['hr.schedule']
        sched = sched_obj.browse(schedule_id)

        vals2 = False
        vals1 = {
            'name': sched.name,
            'employee_id': sched.employee_id.id,
            'template_id': tpl_id,
            'date_start': sched.date_start,
            'date_end': sched.date_end,
        }

        if week_start > sched.date_start:
            dWeekStart = datetime.strptime(week_start, '%Y-%m-%d').date()
            start_day = dWeekStart.strftime('%Y-%m-%d')
            vals1['template_id'] = sched.template_id.id
            vals1['date_end'] = (
                dWeekStart + relativedelta(days=-1)).strftime('%Y-%m-%d')
            vals2 = {
                'name': sched.employee_id.name + ': ' + start_day + ' Wk ' +
                str(dWeekStart.isocalendar()[1]),
                'employee_id': sched.employee_id.id,
                'template_id': tpl_id,
                'date_start': start_day,
                'date_end': sched.date_end,
            }

        sched_obj.unlink(schedule_id)
        # _l.warning('vals1: %s', vals1)
        mail_msg_obj = self.env['mail.message']
        subtype_id = self.env['mail.message.subtype'].search(
            [('name', '=',
              'Discussions')],
            limit=1)
        mail_msg_obj.create({'subject': 'Warning',
                             'body': 'vals1: %s' % (vals1),
                             'model': 'mail.channel',
                             'res_id': 1,
                             'message_type': 'notification',
                             'record_name': 'general',
                             'subtype_id': subtype_id.id or False,
                             })
        sched_obj.create(vals1)
        if vals2:
            # _l.warning('vals2: %s', vals2)
            mail_msg_obj = self.env['mail.message']
            subtype_id = self.env['mail.message.subtype'].search(
                [('name', '=',
                  'Discussions')],
                limit=1)
            mail_msg_obj.create({'subject': 'Warning',
                                 'body': 'vals2: %s' % (vals2),
                                 'model': 'mail.channel',
                                 'res_id': 1,
                                 'message_type': 'notification',
                                 'record_name': 'general',
                                 'subtype_id': subtype_id.id or False,
                                 })
            sched_obj.create(vals2)

    @api.multi
    def _change_by_template(self, employee_id, week_start,
                            new_template_id, doall):

        sched_obj = self.env['hr.schedule']

        schedule_ids = sched_obj.search([
            ('employee_id', '=', employee_id),
            ('date_start', '<=', week_start),
            ('date_end', '>=', week_start),
            ('state', 'not in', ['locked'])])

        # Remove the current schedule and add a new one in
        # its place according to
        # the new template
        if len(schedule_ids) > 0:
            self._remove_add_schedule(schedule_ids[0], week_start,
                                      new_template_id)

        # Also, change all subsequent schedules if so directed
        if doall:
            ids = sched_obj.search([('employee_id', '=', employee_id),
                                    ('date_start', '>', week_start),
                                    ('state', 'not in', ['locked'])])
            for i in ids:
                self._remove_add_schedule(i, week_start, new_template_id)

    @api.multi
    def change_restday(self):

        for data in self:
            # Change the rest day for only one schedule
            if data.temp_restday and data.dayofweek and data.temp_week_start:
                self._change_restday(data.employee_id.id, data.temp_week_start,
                                     data.dayofweek)

            # Change entire week's schedule to the chosen schedule template
            if not data.temp_restday and data.st_new_id and data.week_start:

                if data.week_start:
                    self._change_by_template(data.employee_id.id,
                                             data.week_start,
                                             data.st_new_id.id, data.permanent)

                # If this change is permanent modify employee's contract
                # to reflect the new template
                if data.permanent:
                    data.contract_id.write({'schedule_template_id':
                                            data.st_new_id.id})

            return {
                'name': 'Change Schedule Template',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.restday.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': self._context
            }
