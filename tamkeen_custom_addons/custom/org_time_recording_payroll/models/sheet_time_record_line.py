from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DTFORMAT


class SheetTimeRecordingLine(models.Model):
    _name = "sheet.time.recording.line"
    _description = 'Timesheet Line'

    def change_colore_on_kanban(self):
        for record in self:
            color = 0
            if record.state == 'draft':
                color = 2
            elif record.state == 'confirm':
                color = 3
            elif record.state == 'assign_to_payroll':
                color = 4
            elif record.state == 'on_hold':
                color = 5
            elif record.state == 'new_joiner':
                color = 6
            elif record.state == 'simulated':
                color = 7
            else:
                color = 7
            record.color = color

    def _get_shift(self):
        shift_timeline_obj = self.env['shift.timeline']
        shift_rec = False
        for rec in self:
            shift_rec = shift_timeline_obj._get_shift(rec.employee_id)
        return shift_rec

    def _get_rest_days(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    @api.multi
    def _get_overtime_hours(self):
        overtime_claim_obj = self.env['overtime.claim.activity']
        for rec in self:
            total_overtime_hours = 0.0
            if not rec.affected_payroll:
                overtime_claim_rec = overtime_claim_obj.search([
                    ('date', '=', rec.date), ('employee_id', '=',
                                              rec.employee_id.id)],
                    order='id desc', limit=1)
                if overtime_claim_rec:
                    total_overtime_hours += overtime_claim_rec.calculated_hours
            rec.overtime_hours = total_overtime_hours

    def _check_employee_leave(self):
        holidays_obj = self.env['hr.holidays']
        start_date, end_date = self._get_start_end_date(self.date)
        holidays_rec = holidays_obj.search([
            ('employee_id', '=', self.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '>=', start_date),
            ('date_to', '<=', end_date),
            ('state', '=', 'validate')], limit=1)
        return holidays_rec

    # @api.multi
    # def _get_total_leave_hours(self):
    #     holidays_obj = self.env['hr.holidays']
    #     for rec in self:
    #         leave_hours = 0.0
    #         shift_rec = rec._get_shift()
    #         if not rec.affected_payroll and shift_rec:
    #             start_date, end_date = self._get_start_end_date(rec.date)
    #             holidays_rec = holidays_obj.search([
    #                 ('employee_id', '=', rec.employee_id.id),
    #                 ('type', '=', 'remove'),
    #                 ('holiday_status_id.code', '!=', 'UNP'),
    #                 ('date_from', '>=', start_date),
    #                 ('date_to', '<=', end_date),
    #                 ('state', '=', 'validate')], limit=1)
    #             if holidays_rec:
    #                 leave_hours = self._get_leave_schedule_hours(rec.date,
    #                                                              shift_rec)
    #         rec.leave_hours = leave_hours

    def _get_total_unpaid_leave_hours(self):
        holidays_obj = self.env['hr.holidays']
        for rec in self:
            leave_hours = 0.0
            shift_rec = rec._get_shift()
            if not rec.affected_payroll and shift_rec:
                start_date, end_date = self._get_start_end_date(rec.date)
                holidays_rec = holidays_obj.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('type', '=', 'remove'),
                    ('holiday_status_id.code', '=', 'UNP'),
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('state', '=', 'validate')], limit=1)
                if holidays_rec:
                    leave_hours = self._get_leave_schedule_hours(rec.date,
                                                                 shift_rec)
            rec.unpaid_leave_hours = leave_hours
            rec.total_unpaid_hours = leave_hours

    @api.multi
    def _get_total_working_hours(self):
        attendance_obj = self.env['hr.attendance']
        public_holiday_obj = self.env['hr.holidays.public']
        for rec in self:
            working_hours = 0.0
            additional_hours = 0.0
            rest_days = rec._get_rest_days(rec.employee_id)
            recording_date = datetime.strptime(rec.date, OE_DTFORMAT)
            attendance_rec = attendance_obj.search([('date', '=', rec.date),
                                                    ('employee_id', '=',
                                                     rec.employee_id.id),
                                                    ('status', '=', 'CORRECT')
                                                    ], order='id desc',
                                                   limit=1)
            if attendance_rec and recording_date.weekday() in \
                    rest_days or (
            public_holiday_obj.is_public_holiday(rec.date)):
                additional_hours += attendance_rec.worked_hours
            else:
                working_hours += attendance_rec.worked_hours
            rec.working_hours = working_hours
            if rec.working_hours > rec.schedule_hours:
                additional_hours = rec.working_hours - rec.schedule_hours
            rec.additional_hours = additional_hours

    @api.multi
    @api.depends('working_hours', 'adjusted_hours', 'off_hours')
    def _get_total_paid_hours(self):
        for rec in self:
            shift_rec = rec._get_shift()
            total_paid_hours, schedule_hours = 0.0, 0.0
            if shift_rec:
                schedule_hours = shift_rec.default_scheduled_hours
                total_paid_hours += rec.working_hours + rec.adjusted_hours + \
                                    rec.off_hours
            rec.schedule_hours = schedule_hours
            rec.total_paid_hours = total_paid_hours

    # @api.multi
    # def _get_total_paid_hours(self):

    # @api.depends('total_paid_hours')
    # def _get_total_store_paid_hours(self):
    #     for rec in self:
    #         rec.store_total_paid_hours = rec.total_paid_hours

    def _get_day_status(self):
        public_holiday_obj = self.env['hr.holidays.public']
        for rec in self:
            off_hours, day_status = 0.0, ''
            shift_rec = rec._get_shift()
            rest_days = rec._get_rest_days(rec.employee_id)
            recording_date = datetime.strptime(rec.date, OE_DTFORMAT)
            if shift_rec:
                if recording_date.weekday() in rest_days:
                    day_status += 'Rest Day'
                    off_hours += shift_rec.default_scheduled_hours
                elif (
                    public_holiday_obj.is_public_holiday(rec.date)):
                    day_status += 'Public Holiday'
                    off_hours += shift_rec.default_scheduled_hours
                elif rec._check_employee_leave():
                    day_status += 'Leave'
                    off_hours += shift_rec.default_scheduled_hours
                else:
                    day_status += 'Normal Day'
            rec.off_hours = off_hours
            rec.day_status = day_status

    @api.multi
    def _get_total_additional_absence_hours(self):
        for rec in self:
            # if rec.working_hours > rec.schedule_hours:
            #     rec.additional_hours = rec.working_hours - rec.schedule_hours
            if rec.working_hours < rec.schedule_hours:
                rec.absence_hours = rec.schedule_hours - rec.working_hours

    # @api.multi
    # def _get_public_holidays_hours(self):
    #     public_holiday_hours = 0.0
    #     public_holiday_obj = self.env['hr.holidays.public']
    #     shift_timeline_obj = self.env['shift.timeline']
    #     for rec in self:
    #         shift_rec = shift_timeline_obj._get_shift(rec.employee_id)
    #         if rec.date and (public_holiday_obj.is_public_holiday(
    #                 rec.date)):
    #             public_holiday_hours = shift_rec.default_scheduled_hours
    #         rec.public_holiday_hours = public_holiday_hours

    date = fields.Date(string='Date', index=True)
    schedule_hours = fields.Float('Scheduled Hours', copy=False,
                                  compute='_get_total_paid_hours', store=True)
    working_hours = fields.Float('Working Hours (Attendance, Onsite)',
                                 copy=False,
                                 compute='_get_total_working_hours')
    # public_holiday_hours = fields.Float('Public Holiday Hours', copy=False,
    #                                     compute='_get_public_holidays_hours')
    # leave_hours = fields.Float('Paid Leave Hours', copy=False,
    #                            compute='_get_total_leave_hours')
    unpaid_leave_hours = fields.Float('Unpaid Leave Hours', copy=False,
                                      compute='_get_total_unpaid_leave_hours')
    absence_hours = fields.Float('Missing Hours', copy=False,
                                 compute='_get_total_additional_absence_hours')
    additional_hours = fields.Float('Additional Hour', copy=False,
                                    compute='_get_total_working_hours')
    adjusted_hours = fields.Float('Adjusted Hour', copy=False)
    overtime_hours = fields.Float('Overtime Hours', copy=False,
                                  compute='_get_overtime_hours')
    total_paid_hours = fields.Float('Total Paid Hours', copy=False,
                                    compute='_get_total_paid_hours',
                                    store=True)
    # store_total_paid_hours = fields.Float('Total Paid Hours', copy=False,
    #                                 compute='_get_total_store_paid_hours',
    #                                       store=True)
    total_unpaid_hours = fields.Float('Total UnPaid Hours', copy=False,
                                      compute='_get_total_unpaid_leave_hours')
    off_hours = fields.Float('Off Hours', copy=False,
                                      compute='_get_day_status')
    day_status = fields.Char('Day Status', copy=False,
                             compute='_get_day_status')
    payroll_locked = fields.Boolean(string='Payroll Locked?', copy=False)
    payroll_locked_date = fields.Date(string='Lock Date', copy=False)
    affected_payroll = fields.Boolean('Affected Payroll?', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False)
    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet',
                               string='Timesheet', copy=False)
    timesheet_hours = fields.Float(string='Timesheet Hours', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                               ('assign_to_payroll',
                                'Assign to Payroll Period'),
                               ('on_hold', 'On Hold'),
                               ('new_joiner', 'New Joiner'),
                               ('simulated', 'Simulated')],
                              string='Status', default='draft')
    color = fields.Integer('Color Index', compute="change_colore_on_kanban",
                           store=True)
    log_ids = fields.One2many('time.recording.log', 'time_record_id',
                              string='Time Recording Log/s')
    previous_state = fields.Char(string='Prvious State')

    def add_stage_log(self):
        # Add Stage log
        context = dict(self._context)
        state_to = context and context.get('state') or ''
        stage_log_obj = self.env['time.recording.log']
        stage_log_obj.create({'time_record_id': self.id,
                              'state_from': dict(
                                  self._fields['state'].selection).get(
                                  self.state),
                              'state_to': dict(self._fields['state'].selection).get(
                                  state_to),
                              'user_id': self._uid,
                              'activity_datetime':
                                  datetime.now().strftime(OE_DATETIMEFORMAT),
                              })

    def _get_leave_schedule_hours(self, time_record_date, shift_rec):
        leave_schedule_hours = 0.0
        date_from_strp = \
            datetime.strptime(time_record_date, OE_DTFORMAT)
        public_holiday_obj = self.env['hr.holidays.public']
        if time_record_date and (public_holiday_obj.is_public_holiday(
                time_record_date)):
            return leave_schedule_hours
        for line in shift_rec.attendance_ids:
            if int(date_from_strp.weekday()) == int(line.dayofweek):
                leave_schedule_hours = line.scheduled_hours
        return leave_schedule_hours

    @api.model
    def default_get(self, fields_list):
        res = super(SheetTimeRecordingLine, self).default_get(fields_list)
        if self._context.get('employee_id'):
            res.update({'employee_id': self._context.get('employee_id')})
        return res

    def _get_start_end_date(self, date):
        start_date = str(date) + ' 00:00:00'
        end_date = str(date) + ' 23:59:59'
        return start_date, end_date

    # def _get_schedule_hours(self, employee, date, shift_rec):
    #     attendance_obj = self.env['hr.attendance']
    #     schedule_hours, additional_hours, absence_hours, working_hours = \
    #         0.0, 0.0, 0.0, 0.0
    #     if shift_rec:
    #         schedule_hours = shift_rec.default_scheduled_hours
    #         # if ':' in schedule_hours:
    #         #     schedule_hours = float(schedule_hours.split(':')[0])
    #     attendance_rec = attendance_obj.search([('date', '=', date),
    #                                             ('employee_id', '=',
    #                                              employee.id)])
    #     if attendance_rec:
    #         working_hours = attendance_rec.worked_hours
    #         # if ':' in working_hours:
    #         #     working_hours = float(working_hours.split(':')[0])
    #     if working_hours > schedule_hours:
    #         additional_hours = working_hours - schedule_hours
    #     if working_hours < schedule_hours:
    #         absence_hours = schedule_hours - working_hours
    #     return working_hours, schedule_hours, additional_hours, absence_hours

    @api.multi
    def create_timesheet_record_line(self):
        vals, timesheet_record_line = {}, []
        employee_obj = self.env['hr.employee']
        shift_timeline_obj = self.env['shift.timeline']
        today_date = date.today()
        for employee in employee_obj.search([('active', '=', True)]):
            # total_unpaid_hours = 0.0
            shift_rec = shift_timeline_obj._get_shift(employee)
            if self.search([('employee_id', '=', employee.id),
                            ('date', '=', today_date)]):
                continue
            if not shift_rec:
                continue
            # public_holiday_hours = self.\
            #     _get_public_holidays_hours(today_date, shift_rec)
            # total_overtime_hours = self._get_overtime_hours(employee,
            #                                                 today_date)
            # working_hours, schedule_hours, additional_hours, absence_hours = \
            #     self._get_schedule_hours(employee, today_date, shift_rec)
            # leave_hours = self._get_total_leave_hours(employee, today_date, shift_rec)
            # unpaid_leave_hours = self._get_total_unpaid_leave_hours(employee,
            #                                                today_date, shift_rec)
            # payroll_lock_period_rec = \
            #     self.search([('date', '=', previous_date),
            #                  ('employee_id', '=', employee.id),
            #                  ('payroll_locked', '=', True)])
            # total_paid_hours = float(schedule_hours)
            # if payroll_lock_period_rec:
            #     total_unpaid_hours = float(total_overtime_hours)
            # else:
            #      total_paid_hours += float(total_overtime_hours)
            vals.update({
                'employee_id': employee.id,
                'date': today_date,
                # 'leave_hours': leave_hours,
                # 'public_holiday_hours': public_holiday_hours,
                # 'working_hours': working_hours,
                # 'total_paid_hours': total_paid_hours,
                # 'total_unpaid_hours': total_unpaid_hours,
                # 'schedule_hours': schedule_hours,
                # 'additional_hours': additional_hours,
                # 'overtime_hours': total_overtime_hours,
                # 'absence_hours': absence_hours,
                # 'unpaid_leave_hours': unpaid_leave_hours
            })
            self.create(vals)
        return True