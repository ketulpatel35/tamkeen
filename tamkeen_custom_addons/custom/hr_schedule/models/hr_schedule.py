from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc
from datetime import datetime, timedelta
from odoo.exceptions import Warning
import time

DAYOFWEEK_SELECTION = [('0', 'Monday'),
                       ('1', 'Tuesday'),
                       ('2', 'Wednesday'),
                       ('3', 'Thursday'),
                       ('4', 'Friday'),
                       ('5', 'Saturday'),
                       ('6', 'Sunday'),
                       ]

class HrScheduleAlert(models.Model):
    _name = 'hr.schedule.alert'
    _description = 'Attendance Exception'
    _inherit = ['mail.thread', 'resource.calendar']

    @api.multi
    def _get_employee_id(self):
        for alert in self:
            if alert.punch_id:
                alert.employee_id = alert.punch_id.employee_id.id
            elif alert.sched_detail_id:
                alert.employee_id = \
                    alert.sched_detail_id.schedule_id.employee_id.id
            else:
                alert.employee_id = False

    def _search_upper(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('id', operator, value)]

    name = fields.Datetime(string='Date and Time')
    rule_id = fields.Many2one('hr.schedule.alert.rule', string='Alert Rule')
    punch_id = fields.Many2one('hr.attendance', string='Triggering Punch')
    sched_detail_id = fields.Many2one(
        'hr.schedule.detail',
        string='Schedule Detail')
    employee_id = fields.Many2one(
        'hr.employee',
        compute='_get_employee_id',
        method=True,
        string='Employee',
        search='_search_upper')
    department_id = fields.Many2one(
        related='employee_id.department_id',
        store=True,
        string='Department')
    severity = fields.Selection(
        related='rule_id.severity',
        string='Severity',
        store=True)
    state = fields.Selection((
        ('unresolved', 'Unresolved'),
        ('resolved', 'Resolved'),
    ), string='State', default='unresolved')

    _sql_constraints = [
        ('all_unique',
         'UNIQUE(punch_id,sched_detail_id,name,rule_id)',
         'Duplicate Record!')]

    @api.model
    def check_for_alerts(self):
        '''Check the schedule detail and attendance records for yesterday
        against the scheduling/attendance alert rules.
        If any rules match create a record in the database.'''

        dept_obj = self.env['hr.department']
        detail_obj = self.env['hr.schedule.detail']
        attendance_obj = self.env['hr.attendance']
        rule_obj = self.env['hr.schedule.alert.rule']

        # XXX - Someone who cares about DST should fix ths
        #
        dtToday = datetime.strptime(
            datetime.now().strftime(OE_DFORMAT) +
            ' 00:00:00',
            OE_DTFORMAT)
        lcldtToday = timezone(
            self.env.user.tz and self.env.user.tz or 'UTC').localize(
            dtToday, is_dst=False)
        utcdtToday = lcldtToday.astimezone(utc)
        utcdtYesterday = utcdtToday + relativedelta(days=-1)
        strToday = utcdtToday.strftime(OE_DTFORMAT)
        strYesterday = utcdtYesterday.strftime(OE_DTFORMAT)
        dept_rec = dept_obj.search([])
        for dept in dept_rec:
            for employee in dept.member_ids:
                # Get schedule and attendance records for the employee for the
                # day
                sched_detail_rec = detail_obj.search([
                    ('schedule_id.employee_id', '=', employee.id), '&',
                    ('date_start', '>=', strYesterday),
                    ('date_start', '<', strToday)], order='date_start')
                attendance_rec = attendance_obj.search([
                    ('employee_id', '=', employee.id), '&',
                    ('check_in', '>=', strYesterday),
                    ('check_out', '<', strToday)], order='check_in')

                # Run the schedule and attendance records against each
                # active rule, and
                # create alerts for each result returned.
                #
                rule_rec = rule_obj.search([('active', '=', True)])
                for rule in rule_rec:
                    res = rule.check_rule(sched_detail_rec,
                                          attendance_rec)

                    for strdt, attendance_id in res.get('punches'):
                        # skip if it has already been triggered
                        ids = self.search([('punch_id', '=', attendance_id),
                                           ('rule_id', '=', rule.id),
                                           ('name', '=', strdt),
                                           ])
                        if len(ids) > 0:
                            continue
                        self.create({'name': strdt,
                                     'rule_id': rule.id,
                                     'punch_id': attendance_id})

                    for strdt, detail_id in res.get('schedule_details'):
                        # skip if it has already been triggered
                        ids = self.search([('sched_detail_id', '=', detail_id),
                                           ('rule_id', '=', rule.id),
                                           ('name', '=', strdt)])
                        if len(ids) > 0:
                            continue
                        self.create({'name': strdt,
                                     'rule_id': rule.id,
                                     'sched_detail_id': detail_id})

    @api.multi
    def _get_normalized_attendance(self, employee_id, utcdt, att_rec):
        att_obj = self.env['hr.attendance']
        strToday = utcdt.strftime(OE_DTFORMAT)
        # If the first punch is a punch-out then get the corresponding punch-in
        # from the previous day.
        if len(att_rec) > 0 and not att_rec[0].check_in:
            strYesterday = (utcdt - timedelta(days=1)).strftime(OE_DTFORMAT)
            att2 = att_obj.search([('employee_id', '=', employee_id),
                                   '&', ('name', '>=', strYesterday),
                                   ('name', '<', strToday)], order='name')
            if len(att2) > 0 and att2[-1].action == 'sign_in':
                att_ids = [att2[-1].id] + att_rec.ids
            else:
                att_ids = att_rec.ids[1:]

        # If the last punch is a punch-in then get the corresponding punch-out
        # from the next day.
        if len(att_rec) > 0 and not att_rec[-1].check_out:
            strTommorow = (utcdt + timedelta(days=1)).strftime(OE_DTFORMAT)
            att2 = att_obj.search([('employee_id', '=', employee_id),
                                   '&', ('name', '>=', strToday),
                                   ('name', '<', strTommorow)], order='name')
            if len(att2) > 0 and att2[0].action == 'sign_out':
                att_ids = att_ids + [att2[0].id]
            else:
                att_ids = att_ids[:-1]
            return att_ids

    @api.multi
    def compute_alerts_by_employee(self, employee_id, strDay):
        '''Compute alerts for employee on specified day.'''

        attendance_obj = self.env['hr.attendance']
        rule_obj = self.env['hr.schedule.alert.rule']
        detail_obj = self.env['hr.schedule.detail']
        # XXX - Someone who cares about DST should fix ths
        #
        dt = datetime.strptime(strDay + ' 00:00:00', OE_DTFORMAT)
        if self.env.user and self.env.user.tz:
            lcldt = timezone(self.env.user.tz).localize(dt, is_dst=False)
            utcdt = lcldt.astimezone(utc)
            utcdtNextDay = utcdt + relativedelta(days=+1)
            strToday = utcdt.strftime(OE_DTFORMAT)
            strNextDay = utcdtNextDay.strftime(OE_DTFORMAT)

            # Get schedule and attendance records for the employee for the day
            sched_detail_rec = detail_obj.search(
                [
                    ('schedule_id.employee_id',
                     '=',
                     employee_id),
                    '&',
                    ('day',
                     '>=',
                     strToday),
                    ('day',
                     '<',
                     strNextDay),
                ],
                order='date_start')
            attendance_rec = attendance_obj.search([
                ('employee_id', '=', employee_id), '&',
                ('check_in', '>=', strToday),
                ('check_out', '<', strNextDay)], order='check_in')
            attendance_rec = self._get_normalized_attendance(
                employee_id, utcdt, attendance_rec)

            # Run the schedule and attendance records
            #  against each active rule, and
            # create alerts for each result returned.
            rule_rec = rule_obj.search([('active', '=', True)])
            for rule in rule_rec:
                res = rule.check_rule(sched_detail_rec,
                                      attendance_rec)

                for strdt, attendance_id in res.get('punches'):
                    # skip if it has already been triggered
                    ids = self.search([('punch_id', '=', attendance_id),
                                       ('rule_id', '=', rule.id),
                                       ('name', '=', strdt)])

                    if len(ids) > 0:
                        continue
                    self.create({'name': strdt,
                                 'rule_id': rule.id,
                                 'punch_id': attendance_id})

                for strdt, detail_id in res.get('schedule_details'):
                    # skip if it has already been triggered
                    ids = self.search([('sched_detail_id', '=', detail_id),
                                       ('rule_id', '=', rule.id),
                                       ('name', '=', strdt)])
                    if len(ids) > 0:
                        continue
                    self.create({'name': strdt,
                                 'rule_id': rule.id,
                                 'sched_detail_id': detail_id})


class HrSchedule(models.Model):
    _name = 'hr.schedule'
    _inherit = ['mail.thread']
    _description = 'Employee Schedule'

    @api.multi
    def _compute_alerts(self):
        for obj in self:
            alert_ids = []
            for detail in obj.detail_ids:
                [alert_ids.append(a.id) for a in detail.alert_ids]
            obj.alert_ids = alert_ids

    name = fields.Char(string="Description")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self:
        self.env['res.company']._company_default_get('hr.schedule'))
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee')
    template_id = fields.Many2one(
        'hr.schedule.template',
        string='Schedule Template')
    detail_ids = fields.One2many(
        'hr.schedule.detail',
        'schedule_id',
        string='Schedule Detail')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department')
    alert_ids = fields.One2many(
        'hr.schedule.alert',
        compute='_compute_alerts',
        string='Alerts')
    restday_ids1 = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_restdays_rel1',
        'sched_id',
        'weekday_id',
        string='Rest Days Week 1')
    restday_ids2 = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_restdays_rel2',
        'sched_id',
        'weekday_id',
        string='Rest Days Week 2')
    restday_ids3 = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_restdays_rel3',
        'sched_id',
        'weekday_id',
        string='Rest Days Week 3')
    restday_ids4 = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_restdays_rel4',
        'sched_id',
        'weekday_id',
        string='Rest Days Week 4')
    restday_ids5 = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_restdays_rel5',
        'sched_id',
        'weekday_id',
        string='Rest Days Week 5')
    state = fields.Selection((
        ('draft', 'Draft'), (
            'validate', 'Confirmed'),
        ('locked', 'Locked'), (
            'unlocked', 'Unlocked'),
    ), string='State', default='draft')

    @api.constrains('date_start', 'date_end')
    def _schedule_date(self):
        for schedule in self:
            self.env.cr.execute('SELECT id \
                FROM hr_schedule \
                WHERE (date_start <= %s and %s <= date_end) \
                    AND employee_id=%s \
                    AND id <> %s', (schedule.date_end, schedule.date_start,
                                    schedule.employee_id.id, schedule.id))
            if self.env.cr.fetchall():
                raise Warning(_('You cannot have schedules that overlap!'))

    # Call From HR Payroll Extenstion and HR Holidays Extension
    def get_rest_days(self, employee_id, dt):
        '''If the rest day(s) have been explicitly specified that's what is
        returned, otherwise a guess is returned based on the week days that
        are not scheduled. If an explicit rest day(s) has not been specified
        an empty list is returned. If it is able to figure out the rest days
        it will return a list of week day integers with Monday being 0.'''

        day = dt.strftime(OE_DTFORMAT)
        shedule_rec = self.search([('employee_id', '=', employee_id),
                                   ('date_start', '<=', day),
                                   ('date_end', '>=', day)])
        if len(shedule_rec) == 0:
            return None
        elif len(shedule_rec) > 1:
            raise Warning(
                _('Employee has a scheduled date in more than one schedule.'))

        # If the day is in the middle of the week get the start of the week
        if dt.weekday() == 0:
            week_start = dt.strftime(OE_DFORMAT)
        else:
            week_start = (
                dt + relativedelta(days=-dt.weekday())).strftime(OE_DFORMAT)
        return shedule_rec[0].get_rest_days_by_id(week_start)

    @api.multi
    def get_rest_days_by_id(self, week_start):
        '''If the rest day(s) have been explicitly specified that's what is
        returned, otherwise a guess is returned based on the week days that
        are not scheduled. If an explicit rest day(s) has not been specified
        an empty list is returned. If it is able to figure out the rest days
        it will return a list of week day integers with Monday being 0.'''

        res = []

        # Set the boundaries of the week (i.e- start of current week and
        # start of next week)
        #
        if not self.detail_ids:
            return res
        dtFirstDay = datetime.strptime(
            self.detail_ids[0].date_start, OE_DTFORMAT)
        date_start = dtFirstDay.strftime(OE_DFORMAT) < week_start and \
            week_start + ' ' + dtFirstDay.strftime(
            '%H:%M:%S') or dtFirstDay.strftime(OE_DTFORMAT)
        dtNextWeek = datetime.strptime(
            date_start, OE_DTFORMAT) + relativedelta(weeks=+1)

        # Determine the appropriate rest day list to use
        #
        restday_ids = False
        dSchedStart = datetime.strptime(self.date_start, OE_DFORMAT).date()
        dWeekStart = datetime.strptime(week_start, OE_DFORMAT).date()
        if dWeekStart == dSchedStart:
            restday_ids = self.restday_ids1
        elif dWeekStart == dSchedStart + relativedelta(days=+7):
            restday_ids = self.restday_ids2
        elif dWeekStart == dSchedStart + relativedelta(days=+14):
            restday_ids = self.restday_ids3
        elif dWeekStart == dSchedStart + relativedelta(days=+21):
            restday_ids = self.restday_ids4
        elif dWeekStart == dSchedStart + relativedelta(days=+28):
            restday_ids = self.restday_ids5

        # If there is explicit rest day data use it, otherwise try to
        # guess based on which
        # days are not scheduled.
        #
        if restday_ids:
            res = [rd.sequence for rd in restday_ids]
        else:
            weekdays = ['0', '1', '2', '3', '4', '5', '6']
            scheddays = []
            for dtl in self.detail_ids:
                # Make sure the date we're examining isn't in the previous week
                # or the next one
                if dtl.date_start < week_start or datetime.strptime(
                        dtl.date_start, OE_DTFORMAT) >= dtNextWeek:
                    continue
                if dtl.dayofweek not in scheddays:
                    scheddays.append(dtl.dayofweek)
            res = [int(d) for d in weekdays if d not in scheddays]
            # If there are no sched.details return nothing instead of *ALL* the
            # days in the week
            if len(res) == 7:
                res = []
        return res

    @api.onchange('employee_id', 'date_start')
    def onchange_employee_start_date(self):
        dStart = False
        if self.date_start:
            dStart = datetime.strptime(self.date_start, OE_DFORMAT).date()
            # The schedule must start on a Monday
            if dStart.weekday() != 0:
                self.date_start = False
                self.date_end = False
            else:
                dEnd = dStart + relativedelta(days=+6)
                self.date_end = dEnd.strftime(OE_DFORMAT)
        if self.employee_id:
            if self.employee_id.name:
                self.name = self.employee_id.name
                if dStart:
                    self.name += ': ' + \
                                 dStart.strftime(OE_DFORMAT) + ' Wk ' + \
                                 str(dStart.isocalendar()[1])
            if self.employee_id.contract_id and \
                    self.employee_id.contract_id.working_hours:
                self.template_id = \
                    self.employee_id.contract_id.working_hours

    @api.multi
    def delete_details(self):
        for rec in self:
            rec.detail_ids.unlink()

    @api.model
    def add_restdays(self, field_name, rest_days=None):
        restday_ids = []
        if rest_days is None:
            for rd in self.template_id.restday_ids:
                restday_ids.append(rd.id)
        else:
            restday_ids = self.env['hr.schedule.weekday'].search(
                [('sequence', 'in', rest_days)])
        if len(restday_ids) > 0:
            self.write({field_name: [(6, 0, restday_ids)]})

    @api.multi
    def create_details(self):
        leave_obj = self.env['hr.holidays']
        for rec in self:
            if rec.template_id:
                leaves = []
                leave_rec = leave_obj.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('date_from', '<=', rec.date_end),
                    ('date_to', '>=', rec.date_start),
                    ('state', 'in', ['draft', 'validate', 'validate1'])]
                )
                for lv in leave_rec:
                    utcdtFrom = utc.localize(datetime.strptime(
                        lv.date_from, OE_DTFORMAT), is_dst=False)
                    utcdtTo = utc.localize(
                        datetime.strptime(
                            lv.date_to,
                            OE_DTFORMAT),
                        is_dst=False)
                    leaves.append((utcdtFrom, utcdtTo))
                if not self.env.user.tz:
                    # _logger.warning(
                    #     'You have to set timezone first')
                    mail_msg_obj = self.env['mail.message']
                    subtype_id = self.env['mail.message.subtype'].search([
                        ('name', '=', 'Discussions')], limit=1)
                    mail_msg_obj.create({'subject': 'Warning',
                                         'body': 'You have to set timezone '
                                                 'first',
                                         'model': 'mail.channel',
                                         'res_id': 1,
                                         'message_type': 'notification',
                                         'record_name': 'general',
                                         'subtype_id': subtype_id.id or False,
                                         })
                if self.env.user.tz:
                    local_tz = timezone(self.env.user.tz)
                dCount = datetime.strptime(rec.date_start, OE_DFORMAT).date()
                dCountEnd = datetime.strptime(rec.date_end, OE_DFORMAT).date()
                dWeekStart = dCount
                dSchedStart = dCount
                while dCount <= dCountEnd:

                    # Enter the rest day(s)
                    #
                    if dCount == dSchedStart:
                        rec.add_restdays('restday_ids1')
                    elif dCount == dSchedStart + relativedelta(days=+7):
                        rec.add_restdays('restday_ids2')
                    elif dCount == dSchedStart + relativedelta(days=+14):
                        rec.add_restdays('restday_ids3')
                    elif dCount == dSchedStart + relativedelta(days=+21):
                        rec.add_restdays('restday_ids4')
                    elif dCount == dSchedStart + relativedelta(days=+28):
                        rec.add_restdays('restday_ids5')

                    prevutcdtStart = False
                    prevDayofWeek = False
                    for worktime in rec.template_id.worktime_ids:
                        hour, sep, minute = worktime.hour_from.partition(':')
                        toHour, toSep, toMin = worktime.hour_to.partition(':')
                        if len(sep) == 0 or len(toSep) == 0:
                            raise Warning(
                                _('The time should be entered as HH:MM'))

                        # XXX - Someone affected by DST should fix this
                        #
                        dtStart = datetime.strptime(
                            dWeekStart.strftime(OE_DFORMAT) +
                            ' ' +
                            hour +
                            ':' +
                            minute +
                            ':00',
                            OE_DTFORMAT)
                        locldtStart = local_tz.localize(dtStart, is_dst=False)
                        utcdtStart = locldtStart.astimezone(utc)
                        if worktime.dayofweek != 0:
                            utcdtStart = utcdtStart + \
                                relativedelta(days=+int(
                                    worktime.dayofweek))
                        dDay = utcdtStart.astimezone(local_tz).date()

                        # If this worktime is a continuation (i.e -
                        # after lunch) set the start
                        # time based on the difference from the previous record
                        if prevDayofWeek and \
                                prevDayofWeek == worktime.dayofweek:
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
                        utcdtEnd = utcdtStart + \
                            timedelta(seconds=+delta_seconds)

                        # Leave empty holes where there are leaves
                        #
                        _skip = False
                        for utcdtFrom, utcdtTo in leaves:
                            if utcdtFrom <= utcdtStart and utcdtTo >= utcdtEnd:
                                _skip = True
                                break
                            elif utcdtFrom > utcdtStart and \
                                    utcdtFrom <= utcdtEnd:
                                if utcdtTo == utcdtEnd:
                                    _skip = True
                                else:
                                    utcdtEnd = utcdtFrom + \
                                        timedelta(seconds=-1)
                                break
                            elif utcdtTo >= utcdtStart and utcdtTo < utcdtEnd:
                                if utcdtTo == utcdtEnd:
                                    _skip = True
                                else:
                                    utcdtStart = utcdtTo + \
                                        timedelta(seconds=+1)
                                break
                        if not _skip:
                            val = {
                                'name': rec.name,
                                'dayofweek': worktime.dayofweek,
                                'day': dDay,
                                'date_start': utcdtStart.strftime(
                                    OE_DTFORMAT),
                                'date_end': utcdtEnd.strftime(
                                    OE_DTFORMAT),
                                'schedule_id': rec.id,
                            }
                            rec.write({'detail_ids': [(0, 0, val)]})
                        prevDayofWeek = worktime.dayofweek
                        prevutcdtStart = utcdtStart
                    dCount = dWeekStart + relativedelta(weeks=+1)
                    dWeekStart = dCount
        return True

    @api.model
    def create(self, vals):
        res = super(HrSchedule, self).create(vals)
        res.create_details()
        return res

    @api.model
    def create_mass_schedule(self):
        '''Creates tentative schedules for all employees based on the
        schedule template attached to their contract.
        Called from the scheduler.'''
        ee_obj = self.env['hr.employee']

        # Create a two-week schedule beginning from Monday of next week.
        #
        dt = datetime.today()
        days = 7 - dt.weekday()
        dt += relativedelta(days=+days)
        dStart = dt.date()
        dEnd = dStart + relativedelta(weeks=+2, days=-1)

        # Create schedules for each employee in each department
        #
        dept_rec = self.env['hr.department'].search([])
        for dept in dept_rec:
            ee_rec = ee_obj.search([
                ('department_id', '=', dept.id),
            ], order="name")
            if len(ee_rec) == 0:
                continue
            for ee in ee_rec:
                if not ee.contract_id or not \
                    ee.contract_id.working_hours and \
                        ee.contract_id.state != 'open':
                    continue
                sched = {
                    'name': ee.name + ': ' + dStart.strftime(OE_DFORMAT) +
                    ' Wk ' + str(dStart.isocalendar()[1]),
                    'employee_id': ee.id,
                    'template_id': ee.contract_id.working_hours.id,
                    'date_start': dStart.strftime(OE_DFORMAT),
                    'date_end': dEnd.strftime(OE_DFORMAT),
                }
                self.create(sched)

    @api.one
    def deletable(self):
        if self.state not in ['draft', 'unlocked']:
            return False
        for detail in self.detail_ids:
            if detail.state not in ['draft', 'unlocked']:
                return False
        return True

    @api.multi
    def unlink(self):
        for schedule in self:
            # Do not remove schedules that are not in draft or unlocked state
            if not schedule.deletable():
                continue

            # Delete the schedule details associated with this schedule
            detail_rec = []
            [detail_rec.append(detail) for detail in schedule.detail_ids]
            if len(detail_rec) > 0:
                for details in detail_rec:
                    details.unlink()
        return super(HrSchedule, self).unlink()

    @api.multi
    def action_validate(self):
        for rec in self:
            rec.write({'state': 'validate'})

    @api.multi
    def details_locked(self):

        for sched in self:
            for detail in sched.detail_ids:
                if detail.state != 'locked':
                    return False

        return True

    @api.multi
    def workflow_lock(self):
        '''Lock the Schedule Record. Expects to be called by its schedule
        detail records as they are locked one by one.  When the last one has
        been locked the schedule will also be locked.'''

        all_locked = True
        for sched in self:
            if sched.details_locked():
                sched.state = 'locked'
            else:
                all_locked = False

        return all_locked


class HrScheduleRequest(models.Model):
    _name = 'hr.schedule.request'
    _description = 'Change Request'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date(string='Date')
    type = fields.Selection((
        ('missedp', 'Missed Punch'),
        ('adjp', 'Punch Adjustment'),
        ('absence', 'Absence'),
        ('schedadj', 'Schedule Adjustment'),
        ('other', 'Other')
    ), string='Type')
    message = fields.Text('Message')
    state = fields.Selection((
        ('pending', 'Pending'),
        ('auth', 'Authorized'),
        ('denied', 'Denied'),
        ('cancel', 'Cancelled'),
    ), string='State', default='pending')


class hr_schedule_template(models.Model):
    _name = 'hr.schedule.template'
    _description = 'Employee Working Schedule Template'

    name = fields.Char(string="Name")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self:
        self.env['res.company']._company_default_get('resource.calendar'))
    worktime_ids = fields.One2many(
        'hr.schedule.template.worktime',
        'template_id',
        string='Working Time')
    restday_ids = fields.Many2many(
        'hr.schedule.weekday',
        'schedule_template_restdays_rel',
        'sched_id',
        'weekday_id',
        string='Rest Days')
    # consider_attendance = fields.Boolean(string='Consider Calender for '
    #                                             'Attendance')

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
                    wt.dayofweek for wt in rec.worktime_ids
                    if wt.dayofweek not in scheddays]
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
        for worktime in self.worktime_ids:
            if int(worktime.dayofweek) != day_no:
                continue
            fromHour, fromSep, fromMin = worktime.hour_from.partition(':')
            toHour, toSep, toMin = worktime.hour_to.partition(':')
            if len(fromSep) == 0 or len(toSep) == 0:
                raise Warning(_('Format of working hours is incorrect'))

            delta += datetime.strptime(toHour + ':' + toMin, '%H:%M') - \
                datetime.strptime(fromHour + ':' + fromMin, '%H:%M')

        return float(delta.seconds / 60) / 60.0


class schedule_detail(models.Model):
    _name = "hr.schedule.detail"
    _description = "Schedule Detail"
    _order = 'schedule_id, date_start, dayofweek'

    name = fields.Char("Name")
    dayofweek = fields.Selection(
        DAYOFWEEK_SELECTION,
        string='Day of Week',
        index=True,
        default=0)
    date_start = fields.Datetime(string='Start Date and Time')
    date_end = fields.Datetime(string='End Date and Time')
    day = fields.Date(string='Day', index=True)
    schedule_id = fields.Many2one(
        'hr.schedule',
        string='Schedule')
    department_id = fields.Many2one(
        related='schedule_id.department_id',
        string='Department',
        store=True)
    employee_id = fields.Many2one(
        'hr.employee',
        related='schedule_id.employee_id',
        string='Employee',
        store=True)
    alert_ids = fields.One2many(
        'hr.schedule.alert',
        'sched_detail_id',
        string='Alerts')
    state = fields.Selection((
        ('draft', 'Draft'), (
            'validate', 'Confirmed'),
        ('locked', 'Locked'), (
            'unlocked', 'Unlocked'),
    ), 'State', default='draft')

    @api.constrains('date_start', 'date_end')
    def _detail_date(self):

        for detail in self:
            if not detail.schedule_id.id:
                raise Warning('You can not create Schedule detail Manualy')
            self.env.cr.execute('SELECT id \
                FROM hr_schedule_detail \
                WHERE (date_start <= %s and %s <= date_end) \
                    AND schedule_id=%s \
                    AND id <> %s', (detail.date_end, detail.date_start,
                                    detail.schedule_id.id, detail.id))
            if self.env.cr.fetchall():
                raise Warning(
                    _('You cannot have scheduled days that overlap!'))
        return True

    @api.multi
    def _remove_direct_alerts(self):
        '''Remove alerts directly attached to the schedule detail and
        return a unique list of tuples of employee id and schedule detail
        date.'''

        # Remove alerts directly attached to these schedule details
        alert_ids = []
        scheds = []
        sched_keys = []
        for sched_detail in self:
            [alert_ids.append(alert) for alert in sched_detail.alert_ids]
            # Hmm, creation of this record triggers a workflow action
            # that tries to
            # write to it. But it seems that computed fields aren't
            # available at
            # this stage. So, use a fallback and compute the day ourselves.
            day = sched_detail.day
            if not sched_detail.day:
                day = time.strftime(OE_DFORMAT, time.strptime(
                    sched_detail.date_start, OE_DTFORMAT))
            key = str(sched_detail.schedule_id.employee_id.id) + day
            if key not in sched_keys:
                scheds.append((sched_detail.schedule_id.employee_id.id, day))
                sched_keys.append(key)
        if len(alert_ids) > 0:
            for alert in alert_ids:
                alert.unlink()
        return scheds

    @api.multi
    def scheduled_begin_end_times(self, employee_id, contract_id, dt):
        '''Returns a list of tuples
         containing shift start
          and end times for the day'''

        res = []
        sched_details = self.search([
            ('schedule_id.employee_id.id', '=', employee_id),
            ('day', '=', dt.strftime(
                '%Y-%m-%d')),
        ], order='date_start')
        if len(sched_details) > 0:
            for detail in sched_details:
                res.append((
                    datetime.strptime(
                        detail.date_start, OE_DTFORMAT),
                    datetime.strptime(
                        detail.date_end, OE_DTFORMAT),
                ))

        return res

    @api.multi
    def _recompute_alerts(self, attendances):
        '''Recompute alerts for each record in schedule detail.'''
        alert_obj = self.env['hr.schedule.alert']

        # Remove all alerts for the employee(s) for the day and recompute.
        #
        for ee_id, strDay in attendances:
            # Today's records will be checked tomorrow. Future records can't
            # generate alerts.
            if strDay >= fields.Date.context_today(self):
                continue

            # XXX - Someone who cares about DST should fix this
            #
            dt = datetime.strptime(strDay + ' 00:00:00', OE_DTFORMAT)
            lcldt = timezone(self.env.user.tz).localize(dt, is_dst=False)
            utcdt = lcldt.astimezone(utc)
            utcdtNextDay = utcdt + relativedelta(days=+1)
            strDayStart = utcdt.strftime(OE_DTFORMAT)
            strNextDay = utcdtNextDay.strftime(OE_DTFORMAT)

            alert_rec = alert_obj.search([('employee_id', '=', ee_id),
                                          '&', (
                                              'name', '>=', strDayStart),
                                          ('name', '<', strNextDay)])
            alert_rec.unlink()
            alert_obj.compute_alerts_by_employee(ee_id, strDay)

    @api.model
    def create(self, vals):
        if 'day' not in vals and 'date_start' in vals:
            # XXX - Someone affected by DST should fix this
            #
            local_tz = timezone(self.env.user.tz)

            dtStart = datetime.strptime(vals.get('date_start'), OE_DTFORMAT)
            locldtStart = local_tz.localize(dtStart, is_dst=False)
            utcdtStart = locldtStart.astimezone(utc)
            dDay = utcdtStart.astimezone(local_tz).date()
            vals.update({'day': dDay})

        res = super(schedule_detail, self).create(vals)
        attendances = [
            (res.schedule_id.employee_id.id, fields.Date.context_today(res))]
        self._recompute_alerts(attendances)
        return res

    @api.multi
    def unlink(self):
        schedule_detail_obj = self.env['hr.schedule.detail']
        for detail in self:
            if detail.state in ['draft', 'unlocked']:
                schedule_detail_obj += detail

        attendances = self._remove_direct_alerts()
        res = super(schedule_detail, self).unlink()
        self._recompute_alerts(attendances)
        return res

    @api.multi
    def write(self, vals):
        # Flag for checking wether we have to recompute alerts
        trigger_alert = False
        for k, v in vals.iteritems():
            if k in ['date_start', 'date_end']:
                trigger_alert = True
        if trigger_alert:
            # Remove alerts directly attached to the attendances
            #
            attendances = self._remove_direct_alerts()
        res = super(schedule_detail, self).write(vals)
        if trigger_alert:
            # Remove all alerts for the employee(s) for the day and recompute.
            #
            self._recompute_alerts(attendances)
        return res

    @api.multi
    def workflow_lock(self):

        for detail in self:
            detail.state = 'locked'
            detail.schedule_id.workflow_lock()

        return True


class hr_schedule_alert_rule(models.Model):
    _name = 'hr.schedule.alert.rule'
    _description = 'Scheduling/Attendance Exception Rule'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    severity = fields.Selection((
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ), string='Severity', default='low')
    grace_period = fields.Integer(string='Grace Period',
                                  help='In the case of early '
                                       'or late rules, the amount of time '
                                       'before/after the scheduled time that '
                                       'the rule will trigger.')
    window = fields.Integer(string='Window of Activation')
    active = fields.Boolean(string='Active', default=True)

    @api.multi
    def check_rule(self, sched_details, punches):
        '''Identify if the schedule detail or attendance records
        trigger any rule. If they do return the datetime and id of the
        record that triggered it in one of the appropriate lists.  All
        schedule detail and attendance records are expected to be in sorted
        order according to datetime.'''

        res = {'schedule_details': [], 'punches': []}

        if self.code == 'MISSPUNCH' and punches:
            prev = False
            for punch in punches:
                if not prev:
                    prev = punch
                    if not punch.check_in:
                        res['punches'].append((punch.name, punch.id))
                elif prev.check_in:
                    if not punch.check_out:
                        res['punches'].append((punch.name, punch.id))
                elif prev.check_out:
                    if not punch.check_in:
                        res['punches'].append((punch.name, punch.id))
                prev = punch
            if len(punches) > 0 and not prev.check_out:
                res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'UNSCHEDATT' and punches:
            for punch in punches:
                if punch.check_in:
                    isMatch = False
                    dtPunch = datetime.strptime(
                        punch.check_in, OE_DTFORMAT)
                    for detail in sched_details:
                        dtSched = datetime.strptime(
                            detail.date_start, OE_DTFORMAT)
                        difference = 0
                        if dtSched >= dtPunch:
                            difference = abs((dtSched - dtPunch).seconds) / 60
                        else:
                            difference = abs((dtPunch - dtSched).seconds) / 60
                        if difference < self.window:
                            isMatch = True
                            break
                    if not isMatch:
                        res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'MISSATT' and punches:
            if len(sched_details) > len(punches):
                for detail in sched_details:
                    isMatch = False
                    dtSched = datetime.strptime(
                        detail.date_start, OE_DTFORMAT)
                    for punch in punches:
                        if punch.action == 'sign_in':
                            dtPunch = datetime.strptime(
                                punch.name, OE_DTFORMAT)
                            difference = 0
                            if dtSched >= dtPunch:
                                difference = (dtSched - dtPunch).seconds / 60
                            else:
                                difference = (dtPunch - dtSched).seconds / 60
                            if difference < self.window:
                                isMatch = True
                                break
                    if not isMatch:
                        res['schedule_details'].append(
                            (detail.date_start, detail.id))
        elif self.code == 'UNSCHEDOT' and punches:
            actual_hours = 0
            sched_hours = 0
            for detail in sched_details:
                dtStart = datetime.strptime(
                    detail.date_start, OE_DTFORMAT)
                dtEnd = datetime.strptime(detail.date_end, OE_DTFORMAT)
                sched_hours += float((dtEnd - dtStart).seconds / 60) / 60.0

            dtStart = False
            for punch in punches:
                if punch.check_in:
                    dtStart = datetime.strptime(
                        punch.check_in, OE_DTFORMAT)
                elif punch.check_out:
                    dtEnd = datetime.strptime(punch.name, OE_DTFORMAT)
                    actual_hours += float(
                        (dtEnd - dtStart).seconds / 60) / 60.0
                    if actual_hours > 8 and sched_hours <= 8:
                        res['punches'].append((punch.check_out, punch.id))
        elif self.code == 'TARDY' and punches:
            for detail in sched_details:
                isMatch = False
                dtSched = datetime.strptime(
                    detail.date_start, OE_DTFORMAT)
                for punch in punches:
                    if punch.check_in:
                        dtPunch = datetime.strptime(
                            punch.name, OE_DTFORMAT)
                        difference = 0
                        if dtPunch > dtSched:
                            difference = (dtPunch - dtSched).seconds / 60
                        if difference < self.window and difference > \
                                self.grace_period:
                            isMatch = True
                            break
                if isMatch:
                    res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'LVEARLY' and punches:
            for detail in sched_details:
                isMatch = False
                dtSched = datetime.strptime(
                    detail.date_end, OE_DTFORMAT)
                for punch in punches:
                    if punch.check_out:
                        dtPunch = datetime.strptime(
                            punch.check_out, OE_DTFORMAT)
                        difference = 0
                        if dtPunch < dtSched:
                            difference = (dtSched - dtPunch).seconds / 60
                        if difference < self.window and difference > \
                                self.grace_period:
                            isMatch = True
                            break
                if isMatch:
                    res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'INEARLY' and punches:
            for detail in sched_details:
                isMatch = False
                dtSched = datetime.strptime(
                    detail.date_start, OE_DTFORMAT)
                for punch in punches:
                    if punch.check_in:
                        dtPunch = datetime.strptime(
                            punch.check_in, OE_DTFORMAT)
                        difference = 0
                        if dtPunch < dtSched:
                            difference = (dtSched - dtPunch).seconds / 60
                        if difference < self.window and difference > \
                                self.grace_period:
                            isMatch = True
                            break
                if isMatch:
                    res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'OUTLATE' and punches:
            for detail in sched_details:
                isMatch = False
                dtSched = datetime.strptime(
                    detail.date_end, OE_DTFORMAT)
                for punch in punches:
                    if punch.check_out:
                        dtPunch = datetime.strptime(
                            punch.check_out, OE_DTFORMAT)
                        difference = 0
                        if dtPunch > dtSched:
                            difference = (dtPunch - dtSched).seconds / 60
                        if difference < self.window and difference > \
                                self.grace_period:
                            isMatch = True
                            break
                if isMatch:
                    res['punches'].append((punch.check_in, punch.id))
        elif self.code == 'OVRLP' and punches:
            leave_obj = self.env['hr.holidays']
            for punch in punches:
                if punch.check_in:
                    dtStart = datetime.strptime(
                        punch.check_in, OE_DTFORMAT)
                elif punch.check_out:
                    dtEnd = datetime.strptime(punch.name, OE_DTFORMAT)
                    leave_ids = leave_obj.search([
                        ('employee_id', '=', punch.employee_id.id),
                        ('type', '=', 'remove'),
                        ('date_from', '<=', dtEnd.strftime(OE_DTFORMAT)),
                        ('date_to', '>=', dtStart.strftime(OE_DTFORMAT)),
                        ('state', 'in', ['validate', 'validate1'])])
                    if len(leave_ids) > 0:
                        res['punches'].append((punch.check_in, punch.id))
                        break
        return res


class hr_schedule_working_times(models.Model):
    _name = "hr.schedule.template.worktime"
    _description = "Work Detail"

    name = fields.Char(string="Name")
    dayofweek = fields.Selection(DAYOFWEEK_SELECTION, string='Day of Week',
                                 default='0')
    hour_from = fields.Char(string='Work From')
    hour_to = fields.Char(string="Work To")
    template_id = fields.Many2one('hr.schedule.template',
                                  string='Schedule Template')
    # """ABOVE field(template_id) is Not Used In view"""

    _order = 'dayofweek, name'

    _sql_constraints = [
        ('unique_template_day_from',
         'UNIQUE(template_id, dayofweek, hour_from)', 'Duplicate Records!'),
        ('unique_template_day_to',
         'UNIQUE(template_id, dayofweek, hour_to)', 'Duplicate Records!'),
    ]


# """Because Of Dependency Issue I have put below code in Comment"""
class contract_init(models.Model):
    _inherit = 'hr.contract.init'

    sched_template_id = fields.Many2one('hr.schedule.template',
                                        string='Schedule Template',
                                        states={'draft': [
                                            ('readonly', False)]})


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.model
    def _get_sched_template(self):
        init = self.get_latest_initial_values()
        if init is not None and init.sched_template_id:
            return init.sched_template_id.id

    schedule_template_id = fields.Many2one('hr.schedule.template',
                                           default=_get_sched_template,
                                           string='Working Schedule Template')


class hr_attendance(models.Model):
    _name = 'hr.attendance'
    _inherit = 'hr.attendance'

    alert_ids = fields.One2many('hr.schedule.alert', 'punch_id',
                                string='Exceptions')

    @api.multi
    def _remove_direct_alerts(self):
        '''Remove alerts directly attached to the attendance and return a unique
        list of tuples of employee ids and attendance dates.'''

        # Remove alerts directly attached to the attendances
        #
        alert_ids = []
        attendances = []
        attendance_keys = []
        for attendance in self:
            [alert_ids.append(alert) for alert in attendance.alert_ids]
            key = str(attendance.employee_id.id) + attendance.check_in
            if key not in attendance_keys:
                attendances.append(
                    (attendance.employee_id.id, attendance.check_in))
                attendance_keys.append(key)
        if len(alert_ids) > 0:
            for alert in alert_ids:
                alert.unlink()
        return attendances

    @api.multi
    def _recompute_alerts(self, attendances):
        '''Recompute alerts for each record in attendances.'''

        alert_obj = self.env['hr.schedule.alert']

        # Remove all alerts for the employee(s) for the day and recompute.
        #
        for ee_id, strDay in attendances:

            # Today's records will be checked tomorrow. Future records can't
            # generate alerts.
            if strDay >= fields.Date.context_today:
                continue

            # XXX - Someone who cares about DST should fix this
            #
            dt = datetime.strptime(strDay + ' 00:00:00', OE_DTFORMAT)
            lcldt = timezone(self.env.user.tz).localize(dt, is_dst=False)
            utcdt = lcldt.astimezone(utc)
            utcdtNextDay = utcdt + relativedelta(days=+1)
            strDayStart = utcdt.strftime(OE_DTFORMAT)
            strNextDay = utcdtNextDay.strftime(OE_DTFORMAT)

            alert_ids = alert_obj.search([('employee_id', '=', ee_id), '&',
                                          ('name', '>=', strDayStart),
                                          ('name', '<', strNextDay)])
            alert_ids.unlink()
            alert_obj.compute_alerts_by_employee(ee_id, strDay)

    @api.model
    def create(self, vals):
        res = super(hr_attendance, self).create(vals)
        attendances = [
            (res.employee_id.id, fields.Date.context_today)]
        self._recompute_alerts(attendances)
        return res

    @api.multi
    def unlink(self):
        # Remove alerts directly attached to the attendances
        attendances = self._remove_direct_alerts()
        self._recompute_alerts(attendances)
        return super(hr_attendance, self).unlink()

    @api.multi
    def write(self, vals):
        # Flag for checking wether we have to recompute alerts
        trigger_alert = False
        for k, v in vals.iteritems():
            if k in ['name', 'action']:
                trigger_alert = True

        if trigger_alert:
            # Remove alerts directly attached to the attendances
            attendances = self._remove_direct_alerts()

        if trigger_alert:
            # Remove all alerts for the employee(s) for the day and recompute.
            self._recompute_alerts(attendances)

        return super(hr_attendance, self).write(vals)


class hr_holidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def holidays_validate(self):
        unlink_ids = []
        det_obj = self.env['hr.schedule.detail']
        for leave in self:
            if leave.type != 'remove':
                continue

            det_ids = det_obj.search([
                ('schedule_id.employee_id', '=', leave.employee_id.id),
                ('date_start', '<=', leave.date_to),
                ('date_end', '>=', leave.date_from)],
                order='date_start')
            for detail in det_ids:

                # Remove schedule details completely covered by leave
                if leave.date_from <= detail.date_start and \
                        leave.date_to >= detail.date_end:
                    if detail.id not in unlink_ids:
                        unlink_ids.append(detail)

                # Partial day on first day of leave
                elif leave.date_from > detail.date_start and \
                        leave.date_from <= detail.date_end:
                    dtLv = datetime.strptime(leave.date_from, OE_DTFORMAT)
                    if leave.date_from == detail.date_end:
                        if detail.id not in unlink_ids:
                            unlink_ids.append(detail)
                        else:
                            dtSchedEnd = dtLv + timedelta(seconds=-1)
                            det_obj.write(detail.id, {
                                'date_end': dtSchedEnd.strftime(OE_DTFORMAT)})

                # Partial day on last day of leave
                elif leave.date_to < detail.date_end and \
                        leave.date_to >= detail.date_start:
                    dtLv = datetime.strptime(leave.date_to, OE_DTFORMAT)
                    if leave.date_to != detail.date_start:
                        dtStart = dtLv + timedelta(seconds=+1)
                        det_obj.write(detail.id, {
                            'date_start': dtStart.strftime(OE_DTFORMAT)})
        unlink_ids.unlink()
        return super(hr_holidays, self).holidays_validate()

    @api.multi
    def holidays_refuse(self):
        sched_obj = self.env['hr.schedule']
        for leave in self:
            if leave.type != 'remove':
                continue

            dLvFrom = datetime.strptime(leave.date_from, OE_DTFORMAT).date()
            dLvTo = datetime.strptime(leave.date_to, OE_DTFORMAT).date()
            sched_ids = sched_obj.search([
                ('employee_id', '=', leave.employee_id.id),
                ('date_start', '<=', dLvTo.strftime(OE_DFORMAT)),
                ('date_end', '>=', dLvFrom.strftime(OE_DFORMAT))])

            # Re-create affected schedules from scratch
            sched_ids.delete_details()
            sched_ids.create_details()
        return super(hr_holidays, self).holidays_refuse()


# """Because OF dependency I have put this code on comment"""
class hr_term(models.Model):
    _inherit = 'hr.employee.termination'

    @api.model
    def create(self, vals):
        det_obj = self.env['hr.schedule.detail']
        res = super(hr_term, self).create(vals)
        if self.env.user and self.env.user.tz:
            local_tz = timezone(self.env.user.tz)
        else:
            local_tz = timezone('Asia/Riyadh')
        dt = datetime.strptime(res.date + ' 00:00:00', OE_DTFORMAT)
        utcdt = (local_tz.localize(dt, is_dst=False)).astimezone(utc)
        det_ids = det_obj.search([
            ('schedule_id.employee_id', '=', res.employee_id.id),
            ('date_start', '>=', utcdt.strftime(OE_DTFORMAT))],
            order='date_start')
        if det_ids:
            det_ids.unlink()
        return res

    @api.multi
    def _restore_schedule(self):
        sched_obj = self.env['hr.schedule']
        for term in self:
            if term.date:
                d = datetime.strptime(term.date, OE_DFORMAT).date()
                sched_ids = sched_obj.search([
                    ('employee_id', '=', term.employee_id.id),
                    ('date_start', '<=', d.strftime(OE_DFORMAT)),
                    ('date_end', '>=', d.strftime(OE_DFORMAT))])

                # Re-create affected schedules from scratch
                sched_ids.delete_details()
                sched_ids.create_details()

    @api.multi
    def state_cancel(self):
        for rec in self:
            rec._restore_schedule()
        return super(hr_term, self).state_cancel()

    @api.multi
    def unlink(self):
        for rec in self:
            rec._restore_schedule()
        return super(hr_term, self).unlink()


class hr_emp(models.Model):
    _inherit = 'hr.employee'
    _description = 'To add the COUNTER of Schedule in the button'

    @api.multi
    def _schedule_count(self):
        for rec in self:
            rec.schedule_count = self.env['hr.schedule'].search_count(
                [('employee_id', '=', rec.id)])

    schedule_count = fields.Integer(compute='_schedule_count',
                                    string='Schedule')
