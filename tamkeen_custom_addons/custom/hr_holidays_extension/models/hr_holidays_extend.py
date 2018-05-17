from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import Warning, ValidationError, UserError
from odoo import tools

from days360 import get_date_diff_days360
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from hijri import Convert_Date
HOURS_PER_DAY = 8


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    _order = 'date_from asc, type desc, write_date asc'

    @api.multi
    def action_approve(self):
        # This is for HR
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        for holiday in self:
            if not self.skip_notifications:
                self._send_email('hr_holidays_extension.'
                                 'email_template_holidays_update_hr')
            holiday.get_approval_info()
            return holiday.write(
                {
                    'state': 'validate1',
                })

    def _get_employee_balance(self, holiday_status_id, employee_id):
        vals = {'current_employee_balance': 0.0, 'locked_balance': 0.0}
        employee_leave_summary_rec = self.env[
            'employee.leave.summary'].search([(
            'holiday_status_id', '=', holiday_status_id.id),
            ('employee_id', '=', employee_id.id)], limit=1)
        if employee_leave_summary_rec:
            vals.update({'current_employee_balance':
                             employee_leave_summary_rec.real_days,
                         'locked_balance': employee_leave_summary_rec.locked_balance
                         })
        return vals

    def _get_max_allowed_annual_balance(self, employee):
        maximum_allowed_annual_balance = 26
        if employee and employee.job_id and \
                employee.job_id.maximum_allowed_annual_balance:
            maximum_allowed_annual_balance = \
                employee.job_id.maximum_allowed_annual_balance
            return maximum_allowed_annual_balance
        return maximum_allowed_annual_balance

    def _get_employee_daily_balance(self, employee):
        maximum_allowed_annual_balance = \
            self._get_max_allowed_annual_balance(employee)
        return round((maximum_allowed_annual_balance / 360), 6)

    def _get_rest_days(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    def _get_shift_for_employee(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        shift_rec = shift_timeline_obj._get_shift(employee)
        return shift_rec

    def _get_default_hours(self, schedule_template):
        default_scheduled_hours = 0.0
        if schedule_template:
            default_scheduled_hours += schedule_template.default_scheduled_hours
        return float(default_scheduled_hours)

    def _get_public_holidays(self, schedule_template):
        hhplo = self.env['hr.holidays.public.line']
        p_holidays_date = []
        if schedule_template:
            for public_holiday in schedule_template.public_holiday_ids:
                if public_holiday.get_holidays_list(public_holiday.year,
                                                    self.employee_id.id):
                    hhplo += public_holiday.get_holidays_list(
                        public_holiday.year,
                        self.employee_id.id)
                for line in hhplo:
                    p_holidays_date.append(line.date)
        return p_holidays_date

    @api.model
    def count_number_of_days_temp(self, from_date=False, till_date=False):
        """
        count number of real days of leave.
        :param holiday: holiday record
        :param till_date: as to date
        :return: number of day
        """
        employee = self.employee_id
        date_from = from_date
        if not date_from:
            if not self.date_from:
                return False
            date_from = datetime.strptime(self.date_from.split(' ')[0],
                                          OE_DATEFORMAT).date()
        date_to = till_date
        if not date_to:
            if not self.date_to:
                return False
            date_to = datetime.strptime(self.date_to.split(' ')[0],
                                        OE_DATEFORMAT).date()

        if (date_from and date_to) and (date_from > date_to):
            raise Warning(
                _('The start date must be anterior to the end date.'))

        # from_weekday = date_from.weekday()
        rest_days = self._get_rest_days(employee)

        # Compute and update the number of days
        number_of_days_temp = 0
        if (date_to and date_from) and (date_from <= date_to):
            td = date_to - date_from
            diff_day = td.days + float(td.seconds) / 86400
            number_of_days_temp = round(math.floor(diff_day)) + 1
        ex_rd = self.holiday_status_id.ex_rest_days
        ex_ph = self.holiday_status_id.ex_public_holidays
        holiday_obj = self.env['hr.holidays.public']
        count_days = number_of_days_temp
        real_days = 0
        ph_days = 0
        r_days = 0
        working_days = 0
        next_dt = date_from
        while count_days > 0:
            public_holiday = holiday_obj.is_public_holiday(next_dt)
            if public_holiday and ex_ph:
                ph_days += 1
            rest_day = (next_dt.weekday() in rest_days and ex_rd)
            if rest_day:
                r_days += 1
            if not rest_day and not public_holiday:
                working_days += 1
                real_days += 1
            next_dt += timedelta(days=+1)
            count_days -= 1
        if date_to:
            return_date = date_to + timedelta(days=+1)
            while (return_date.weekday() in rest_days) or (
                    holiday_obj.is_public_holiday(return_date)):
                return_date = return_date + timedelta(days=+1)
        total_days = working_days + ph_days + r_days
        data = {'total_days': total_days, 'real_days': real_days}
        return data

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self:
            domain = [
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>=', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('type', '=', holiday.type),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(
                    _('You can not have 2 leaves that overlaps on same day!'))

    @api.model
    def _needaction_domain_get(self):
        return False

    @api.multi
    def _set_email_template_context(self):
        ir_model_data = self.env['ir.model.data']
        context = dict(self._context)
        display_link, wr_display_link = False, False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = False
        # window_action_id = window_action_ref = False
        window_action_ref = 'hr_holidays.open_ask_holidays'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            action_id = ir_model_data.get_object_reference(
                addon_name, window_action_id)[1] or False
        if action_id:
            display_link = True
        context.update({
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'hr.holidays',
        })
        return context

    @api.multi
    def _send_email(self, template_xml_ref):
        context = dict(self._context)
        if template_xml_ref:
            addon_name = template_xml_ref.split('.')[0]
            template_xml_id = template_xml_ref.split('.')[1]
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            if self:
                # rec_id = ids[0]
                template_id = \
                    data_pool.get_object_reference(addon_name,
                                                   template_xml_id)[1]
                template_rec = template_pool.browse(template_id)
                if template_rec:
                    email_template_context = self._set_email_template_context()
                    context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
            return True

    @api.multi
    def action_return_wizard(self):
        '''
        Open the wizard for Return Reason
        :return:Wizard
        '''
        for rec in self:
            if rec.type == 'add':
                return rec.write({'state': 'draft'})
            if not rec.can_reset:
                raise UserError(
                    _('Only an HR Manager or'
                      ' the concerned employee'
                      ' can reset to draft.'))
            if rec.state not in \
                    ['confirm', 'refuse', 'validate', 'validate1']:
                raise UserError(
                    _('Leave request state must'
                      ' be "Refused" or "To Approve" in'
                      ' order to reset to Draft.'))
        view = self.env.ref('hr_holidays_extension.refuse_reason_form_view')
        return {
            'name': _('Justification'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refuseleave.reason',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for holiday in self:
            if holiday.holiday_status_id.double_validation:
                req_approvals.append('confirm')
            if holiday.holiday_status_id.hr_appr:
                req_approvals.append('validate1')
            if holiday.holiday_status_id.ceo_appr:
                req_approvals.append('ceo')
            if holiday.holiday_status_id.vp_approval:
                req_approvals.append('vp')
        return req_approvals

    def _get_year_start_last_date(self, date):
        year_start_dt = date.replace(month=1, day=1)
        year_end_dt = date.replace(hour=23, minute=59, second=59,
                                   month=12, day=31)
        return year_start_dt, year_end_dt

    def _get_month_start_last_date(self, date):
        date = datetime.strptime(date, OE_DTFORMAT)
        month_start_dt = date + relativedelta(day=1)
        next_month_start_dt = month_start_dt + relativedelta(months=1)
        month_end_dt = next_month_start_dt - relativedelta(days=1)
        month_start_date_str = datetime.strftime(month_start_dt, OE_DTFORMAT)
        month_end_dt_time = datetime.strftime(month_end_dt, OE_DTFORMAT)
        return month_start_date_str, month_end_dt_time

    def _convert_date_hijri(self, date):
        date = \
            Convert_Date(date, 'english', 'islamic')
        return date

    def _convert_date_english(self, date):
        date = \
            Convert_Date(date, 'islamic', 'english')
        return date

    def _convert_date_from(self, date_from, date_to):
        date_from = datetime.strptime(date_from, OE_DTFORMAT)
        date_to = datetime.strptime(date_to, OE_DTFORMAT)
        return date_from, date_to

    def _get_holiday_rec(self, year_start_dt, year_end_dt):
        year_start_dt = str(year_start_dt).replace(
            str(str(year_start_dt).split(' ')[1]), '00:00:00')
        year_end_dt = str(year_end_dt).replace(
            str(str(year_end_dt).split(' ')[1]), '23:59:59')
        holidays_rec = self.search([
            ('type', '=', 'remove'),
            ('employee_id', '=', self.employee_id.id),
            ('holiday_status_id', '=', self.holiday_status_id.id),
            ('date_from', '>=', year_start_dt),
            ('date_to', '<=', year_end_dt),
            ('state', 'not in', ('draft', 'cancel', 'refuse'))])
        return holidays_rec

    def _get_holiday_rec_with_period(self, month_start_dt, month_end_dt):
        holidays_rec = self.search([('type', '=', 'remove'),
                                    ('employee_id', '=', self.employee_id.id),
                                    ('holiday_status_id', '=',
                                     self.holiday_status_id.id),
                                    ('date_from', '>=', month_start_dt),
                                    ('date_to', '<=', month_end_dt),
                                    ('state', 'not in', ('draft', 'cancel',

                                                         'refuse'))
                                    ])
        return holidays_rec

    def _check_employee_hijri_leaves(self):
        max_days = \
            self.holiday_status_id.max_days
        hijri_date_from = self._convert_date_hijri(str(
            self.date_from).split(' ')[0])
        date_from = datetime.strptime(hijri_date_from, OE_DATEFORMAT)
        hijri_year_start_dt, hijri_year_end_dt = \
            self._get_year_start_last_date(date_from)
        year_start_date_eng = str(self._convert_date_english(str(
            hijri_year_start_dt).split(' ')[0])) + ' 00:00:00'
        year_end_date_eng = str(self._convert_date_english(str(
            hijri_year_end_dt).split(' ')[0])) + ' 23:59:59'
        if self._get_holiday_rec(year_start_date_eng, year_end_date_eng):
            raise Warning(_('You are eligible only for %s day/s per hijri '
                            'year.')% max_days)
        return True

    def _check_max_days_normal_calendar(self):
        max_days = self.holiday_status_id.max_days
        if max_days:
            if self.real_days > max_days:
                raise Warning(_('You are eligible only for %s days per a '
                                'request') % max_days)

    def _check_payroll_period_normal_calendar(self):
        real_days_value = 0.0
        month_start_dt, month_end_dt = self._get_month_start_last_date(
            self.date_from)
        maximum_allowed_days_per_payroll_period = \
            self.holiday_status_id.maximum_allowed_days_per_payroll_period
        holidays_rec = \
            self._get_holiday_rec_with_period(month_start_dt, month_end_dt)
        for holiday in holidays_rec:
            real_days_value += holiday.real_days
        if real_days_value >= maximum_allowed_days_per_payroll_period:
            raise Warning(_('You are eligible only for %s days per a '
                            'month.') % maximum_allowed_days_per_payroll_period)

    def _check_accumulative_balance(self):
        real_days_value = 0.0
        date_from, date_to = self._convert_date_from(self.date_from,
                                                     self.date_to)
        year_start_date, year_last_date = \
            self._get_year_start_last_date(date_from)
        holidays_rec = self._get_holiday_rec(year_start_date, year_last_date)
        for holiday in holidays_rec:
            real_days_value += holiday.real_days
        return real_days_value

    def _check_normal_calendar(self, holiday_status_id):
        if holiday_status_id.max_days <= \
                holiday_status_id.maximum_allowed_days_per_payroll_period:
            if self.holiday_status_id.maximum_allowed_days_per_payroll_period:
                self._check_payroll_period_normal_calendar()
            if holiday_status_id.maximum_allowed_days_per_payroll_period:
                real_days_value = self._check_accumulative_balance()
                if real_days_value > \
                        holiday_status_id.maximum_accumulative_balance_per_calendar:
                    raise Warning(_(
                        'Number of days leave should be greater then Maximum Accumulative Balance Per Calendar'))
        else:
            raise Warning(_('Maximum allowed days per request should be '
                            'greater than or equal to the maximum allowed '
                            'days per payroll period.'))

    @api.multi
    def _maximum_allowed_days_hijri(self):
        max_days = self.holiday_status_id.max_days
        if max_days:
            if self.real_days > max_days:
                raise Warning(_('You are eligible only for %s day/s per a hijri '
                                'year.') % max_days)

    def _get_sick_holiday_rec(self, employee, holiday_status_rec):
        holiday_rec = self.search([('employee_id', '=', employee.id),
                                   ('holiday_status_id', '=', holiday_status_rec.id),
                                   ('state',
                                    'not in',
                                    ('draft',
                                     'refuse',
                                     'cancel')),
                                   ('type', '=', 'remove')
                                   ], order="date_from asc, id asc", limit=1)
        return holiday_rec

    def _get_sick_holiday_rec_date_from(self, employee, holiday_status_rec,
                                        end_year_with_time):
        next_year_holiday_rec = self.search([('employee_id', '=', employee.id),
                                             ('holiday_status_id', '=',
                                              holiday_status_rec.id),
                                             ('date_from', '>=', end_year_with_time),
                                             ('state',
                                              'not in',
                                              ('draft',
                                               'refuse',
                                               'cancel',
                                               )),
                                             ], order="date_from asc, id asc",
                                            limit=1)
        return next_year_holiday_rec

    def _get_sick_holiday_rec_date(self, employee, holiday_status_rec, date_from,
                                   date_to):
        holiday_rec = self.search([('employee_id', '=', employee.id),
                                   ('holiday_status_id', '=',
                                    holiday_status_rec.id),
                                   ('date_from', '>=', date_from),
                                   ('date_to', '<=', date_to),
                                   ('state', 'not in', ('refuse', 'cancel'))
                                   ])
        return holiday_rec

    def _get_end_sick_year(self, date):
        date_from = datetime.strptime(date, OE_DTFORMAT)
        date_to = date_from + relativedelta(years=1)
        return date_from, date_to

    def _get_sick_leave(self, employee, holiday_status_rec, date_from):
        start_year, end_year = self._get_end_sick_year(date_from)
        start_year_with_time = str(start_year).split(' ')[0] + ' 00:00:00'
        end_year_with_time = str(end_year).split(' ')[0] + ' 23:59:59'
        next_year_holiday_rec = \
            self._get_sick_holiday_rec_date_from(employee,
                                                 holiday_status_rec,
                                                 end_year_with_time)
        if next_year_holiday_rec:
            self._get_sick_leave(employee,
                                 holiday_status_rec,
                                 next_year_holiday_rec.date_from)
        else:
            holiday_rec = self._get_sick_holiday_rec_date(employee,
                                                          holiday_status_rec,
                                                          start_year_with_time,
                                                          end_year_with_time)
            number_of_days = 0.0
            if holiday_rec:
                for holiday in holiday_rec:
                    number_of_days += holiday.real_days
                if number_of_days > \
                        holiday_status_rec.maximum_accumulative_balance_per_calendar:
                    raise Warning(_('You are eligible only for %s day/s per '
                                    'a sick calendar.')
                                  % holiday_status_rec.maximum_accumulative_balance_per_calendar)
            return holiday_rec

    def _check_sick_calendar(self, employee, holiday_status_rec):
        if holiday_status_rec.maximum_accumulative_balance_per_calendar:
            holiday_rec = self._get_sick_holiday_rec(employee, holiday_status_rec)
            if holiday_rec:
                date_from = holiday_rec.date_from
                self._get_sick_leave(employee, holiday_status_rec, date_from)
        else:
            raise Warning(_('Kindly ask the HR Team to check the '
                            'configurtion for this leave type.'))

    @api.multi
    def check_leave_allocation(self):
        for rec in self:
            if rec.holiday_status_id.leaves_calculation_calendar:
                if rec.holiday_status_id.leaves_calculation_calendar == \
                                'hijri':
                    rec._check_employee_hijri_leaves()
                    rec._maximum_allowed_days_hijri()
                elif rec.holiday_status_id.leaves_calculation_calendar == \
                        'normal':
                    rec._check_normal_calendar(rec.holiday_status_id)
                    rec._check_max_days_normal_calendar()
                elif rec.holiday_status_id.leaves_calculation_calendar == \
                        'sick':
                    rec._check_sick_calendar(rec.employee_id, rec.holiday_status_id)

    @api.one
    def _get_dest_email_to(self):
        email_to = None
        current_state = self.state
        if current_state == 'confirm':
            email_to = self.employee_id.leave_manager_id.work_email
        elif current_state == 'validate1':
            email_to = self.holiday_status_id.hr_email
        elif current_state == 'ceo':
            email_to = self.employee_id.leave_ceo_id.work_email
        elif current_state == 'vp':
            email_to = self.employee_id.leave_vp_id.work_email
        return email_to

    @api.one
    def _get_approval_delay(self, req_approvals):
        """
        find difference from where approval is pending
        :param rec:
        :param req_approvals:
        :return:
        """
        diff = last_approval_date = False
        current_state_index = req_approvals.index(self.state)
        if current_state_index == 0:
            last_approval_date = self.submit_date
        else:
            previous_state = req_approvals[current_state_index - 1]
            if previous_state == 'confirm':
                last_approval_date = self.mngr_approval_date
            elif previous_state == 'validate':
                last_approval_date = self.hr_approval_date
            elif previous_state == 'ceo':
                last_approval_date = self.ceo_approval_date
        if last_approval_date:
            last_approval_date = datetime.strptime(last_approval_date,
                                                   OE_DTFORMAT).date()
            now = datetime.strptime(self._get_current_datetime(),
                                    OE_DTFORMAT).date()
            diff = relativedelta(now, last_approval_date)
        if diff and diff.days:
            return diff.days
        return diff

    @api.multi
    def send_reminder(self):
        # context = dict(context or {})
        delay_to_remind = 1
        # If there is no any linked reminder criteria,
        # the system will send a daily reminder.
        where_clause = [
            ('state', 'not in', ['draft', 'refuse',
                                 'validate', 'cancel']),
            ('submit_date', '<',
             datetime.now().strftime('%Y-%m-%d 00:00:00'))
        ]
        leave_requested_recs = self.search(where_clause)
        for leave_req_rec in leave_requested_recs:
            req_approvals = leave_req_rec._get_service_req_approvals()
            if leave_req_rec.state in req_approvals:
                # It may happen in case of changing the required approvals
                # before finalizing the pending, so it will be skipped.
                approval_delay_diff = \
                    leave_req_rec._get_approval_delay(req_approvals)
                if leave_req_rec.holiday_status_id.approval_reminder_line:
                    delay_to_remind = leave_req_rec.holiday_status_id. \
                        approval_reminder_line.delay
                else:
                    # default take 1 day
                    delay_to_remind = 1
                if approval_delay_diff > \
                        delay_to_remind:
                    email_to = leave_req_rec._get_dest_email_to()
                    temp_id = 'hr_holidays_extension.' \
                              'leave_req_approval_reminder_cron_email_template'
                    leave_req_rec._send_email(temp_id, email_to,
                                              leave_req_rec.state,
                                              leave_req_rec.id,
                                              'hr_employee_leave')
        return True

    @api.multi
    def action_draft(self):
        context = dict(self._context)
        for holiday in self:
            context.update({'state': 'draft'})
            holiday.with_context(context).add_stage_log()
            holiday.write({'state': 'draft',
                           'repeated_message': False,
                           })
            holiday.get_approval_info()
            linked_requests = holiday.mapped('linked_request_ids')
            for linked_request in linked_requests:
                linked_request.action_draft()
            linked_requests.unlink()
            if holiday.type != 'add':
                template_obj = self.env['mail.template']
                ir_model_data = self.env['ir.model.data']
                # no need to send mail as per client request.
                try:
                    template_id = ir_model_data.get_object_reference(
                        'hr_holidays_extension',
                        'email_template_holidays_update_emp3')[1]
                except ValueError:
                    template_id = False
                if template_id and not self.skip_notifications:
                    template_rec = template_obj.browse(template_id)
                    context = self._set_email_template_context()
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
        return True

    @api.multi
    def name_get(self):
        res, display_name = [], ''
        for record in self:
            if record.employee_id:
                display_name = 'Leave Request From: ' + record.employee_id.name
            res.append((record['id'], display_name))
        return res

    def add_stage_log(self):
        # Add Stage log
        context = dict(self._context)
        state_to = context and context.get('state') or ''
        stage_log_obj = self.env['hr.holidays.log']
        stage_log_obj.create({'leave_id': self.id,
                              'state_from': dict(self._fields['state'].selection).get(self.state),
                              'state_to': dict(self.env['hr.holidays']._fields['state'].selection).get(state_to),
                              'user_id': self._uid,
                              'activity_datetime':
                                  datetime.now().strftime(OE_DTFORMAT),
                              'reason': context.get('reason')
                              })
    @api.multi
    def action_refuse(self):
        """
        Overide default method without super and
        change in some validation.
        :return:
        """
        context = dict(self._context)
        context.update({'state': 'refuse'})
        for holiday in self:
            if self.state not in ['confirm', 'validate', 'validate1', 'vp',
                                  'ceo', 'leave_approved']:
                raise UserError(_('Leave request must be confirmed or '
                                  'validated in order to refuse it.'))
            self._send_email('hr_holidays_extension.'
                             'email_template_holidays_update_emp2')
            self.with_context(context).add_stage_log()
            holiday.write(
                {'state': 'refuse'})
            # Delete the meeting
            if holiday.meeting_id:
                holiday.meeting_id.unlink()
            # If a category that created several holidays, cancel all related
            holiday.linked_request_ids.action_refuse()
        self._remove_resource_leave()
        return True

    @api.multi
    def action_refuse_wizard(self):
        '''
        Open the wizard for Refuse Reason
        :return:Wizard
        '''
        for rec in self:
            if not self.env.user.has_group(
                    'hr_holidays_extension.group_leave_self_approval_srvs') \
                    and rec.state == 'confirm' \
                    and rec.employee_id.user_id.id == self.env.uid:
                raise UserError(_('You cannot refuse your own request.'))
        view = self.env.ref('hr_holidays_extension.refuse_reason_form_view')
        return {
            'name': _('Justification'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refuseleave.reason',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    # refuse_reason = fields.Text(string='Refuse Reason')
    real_days = fields.Float(string='Days of Leave', method=True)
    working_days = fields.Float(
        string='Working Days',
        method=True)
    rest_days = fields.Float(
        string='Rest Days',
        method=True)
    public_holiday_days = fields.Float(
        string='Public Holidays',
        method=True)
    total_days = fields.Float(
        string='Total Days',
        method=True)
    return_date = fields.Char(
        string='Return Date', method=True)
    max_leaves = fields.Float(
        string='Total Allocated Balance',
        method=True)
    leaves_taken = fields.Integer(
        string='Leaves Already Taken',
        method=True)
    remaining_leaves = \
        fields.Float(
            string='Previous Remaining Leaves', method=True)
    curr_remaining_leaves = fields. \
        Float(
        string='Remaining Days', method=True)
    # half_day = fields. \
    #     Boolean(string='Half Day', required=False,
    #             readonly=True, states={'draft': [('readonly', False)],
    #                                    'confirm': [('readonly', False)]})

    # flag_attachment = fields. \
    #     Boolean('Flag Attachment')
    alternative_emp_id = fields. \
        Many2one('hr.employee',
                 string='Alternative Employee')
    # refuse_reason = fields.Text(string='Refuse Reason')
    flag_emp_mandatory = fields. \
        Boolean(string='Flag employee is mandatory')
    nationality_id = fields. \
        Many2one(related='employee_id.country_id',
                 string='Nationality', readonly=True, store=True)
    emp_contract_id = fields. \
        Many2one(related='employee_id.contract_id', string='Contract')
    emp_id = fields.Char(string='Employee ID',
                         related='employee_id.f_employee_no', store=True)

    state = fields.Selection([('draft', 'To Submit'),
                              ('confirm', 'Manager Approval'),
                              ('vp', 'VP Approval'),
                              ('validate1', 'HR Approval'),
                              # ('validate2', 'Senior HR Approval'),
                              ('ceo', 'CEO Approval'),
                              ('leave_approved', 'Validate'),
                              ('validate', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('refuse', 'Refused')],
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             copy=False, help='The status is set'
                                              ' to \'To Submit\','
                                              ' when a holiday request'
                                              ' is created.\\nThe status'
                                              ' is \'To Approve\', when'
                                              ' holiday request is '
                                              'confirmed by user.\\nThe'
                                              ' status is \'Refused\', when'
                                              ' holiday request is refused'
                                              ' by manager.\\nThe status'
                                              ' is \'Approved\', when holiday'
                                              ' request is approved'
                                              ' by manager.', default='draft')

    ex_leave = fields.Boolean(string='Exception Leave', required=False)
    # fix repeated messages issue
    repeated_message = fields. \
        Boolean(string='Repeated Message', invisible=True)

    future_balance = fields.Float(
        string='Future Balance',
        method=True,
        help="The expected reserved leave"
             " days for this employee"
             " in the future until"
             " the leave start date.")
    max_allowed_days = fields.Float(
        string='Request Available Balance',
        help="The sum of employee remaining balance (as of request date)"
             " and the future balance"
             " if this leave type support"
             " calculation in"
             " the future.")  # digits=(16, 2)
    amend = fields.Boolean(string='Amend')
    ori_leave_start = fields.Datetime('Scheduled Start Date', readonly=True)
    ori_leave_end = fields.Datetime('Scheduled End Date', readonly=True)
    actual_number_days = fields.Float('Scheduled No. Days', readonly=True)
    mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                   readonly=True, copy=False)
    vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                 readonly=True, copy=False)
    hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                 readonly=True, copy=False)
    ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                  readonly=True,
                                  copy=False)
    cancelled_user_id = fields.Many2one('res.users', string='Cancelled By',
                                        readonly=True, copy=False)
    refused_user_id = fields.Many2one('res.users', string='Refused By',
                                      readonly=True, copy=False)
    submit_user_id = fields.Many2one('res.users', string='Submitted By',
                                     readonly=True,
                                     copy=False)
    returned_by = fields.Many2one('res.users', string='Returned By',
                                  readonly=True, copy=False)
    amend_by = fields.Many2one('res.users', string='Amend By',
                               readonly=True, copy=False)
    validate_approval_id = fields.Many2one('res.users',
                                           string='Validate Approval',
                                           readonly=True, copy=False)
    final_approval_user_id = fields.Many2one('res.users', string='Final '
                                                                 'Approval',
                                             readonly=True, copy=False)
    mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                         readonly=True, copy=False)
    vp_approval_date = fields.Datetime(string='VP Approval Date',
                                       readonly=True, copy=False)
    hr_approval_date = fields.Datetime(string='HR Approval Date',
                                       readonly=True, copy=False)
    ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                        readonly=True, copy=False)
    cancel_date = fields.Datetime(string='Cancel Date', readonly=True,
                                  copy=False)
    refuse_date = fields.Datetime(string='Refuse Date', readonly=True,
                                  copy=False)
    submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                  copy=False)
    reset_date = fields.Datetime(string='Return Date',
                                 readonly=True, copy=False)
    validate_approval_date = fields.Datetime(string='Validate Approval '
                                                    'Date', readonly=True,
                                             copy=False)
    final_approval_date = fields.Datetime(string='Final Approval Date',
                                          readonly=True, copy=False)
    amendment_date = fields.Datetime(string='Amendment Date', readonly=True,
                                     copy=False)

    skip_notifications = fields.Boolean(string='Skip Notifications',
                                        help="Allow the system to stop "
                                             "sending the notifications.")
    job_id = fields.Many2one('hr.job', string='Position',
                             related='employee_id.job_id')

    department_id = fields.Many2one('hr.department',
                                    related='employee_id.department_id',
                                    string='Organization Unit', readonly=True,
                                    store=True)
    proof_required = fields.Boolean(string='Proof Required')
    leave_proof_ids = fields.One2many('leave.proof.documents', 'leave_id',
                                      string='Leave Proofs')
    about_leave_type = fields.Text(string='About the Leave')
    allocation_type = fields.Selection([('addition', 'Addition'),
                                        ('deduction', 'Deduction')],
                                       string='Allocation Type')
    log_ids = fields.One2many('hr.holidays.log', 'leave_id', string='Leave '
                                                                    'Log/s')
    submit_message = fields.Text(string='Submit Hint Message', store=True)
    active = fields.Boolean(string='Active', default=True)
    # org_unit_type = fields.Selection([('root', 'Root'),
    #                                        ('business', 'Business Unit'),
    #                                        ('department', 'Department'),
    #                                        ('section', 'Section')],
    #                                       related='department_id.org_unit_type',
    #                                       string='Organization Unit Type')

    @api.model
    def _auto_init(self):
        res = super(HrHolidays, self)._auto_init()
        # Remove constrains for vat, nrc on "commercial entities" because is not mandatory by legislation
        # Even that VAT numbers are unique, the NRC field is not unique, and there are certain entities that
        # doesn't have a NRC number plus the formatting was changed few times, so we cannot have a base rule for
        # checking if available and emmited by the Ministry of Finance, only online on their website.

        self.env.cr.execute("""
        alter table hr_job drop CONSTRAINT if exists date_check; """)
        return res

    @api.multi
    def button_amend(self):
        '''
        To do
        Business Validation
        :return:True
        '''
        for rec in self:
            rec.write({'state': 'draft', 'amend': True})
            rec.get_approval_info()
            if rec.holiday_status_id.notif_leave_amend:
                template_obj = self.env['mail.template']
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference(
                        'hr_holidays_extension',
                        'email_template_holidays_amend')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    template_rec = template_obj.browse(template_id)
                    context = self._set_email_template_context()
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
        return True

    @api.multi
    def action_cancel_wizard(self):
        '''
        Open the wizard for Refuse Reason
        :return:Wizard
        '''
        view = self.env.ref('hr_holidays_extension.refuse_reason_form_view')
        return {
            'name': _('Justification'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refuseleave.reason',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def button_cancel(self):
        '''
        To do
        Business Validation
        :return:True
        '''
        context = dict(self._context)
        for rec in self:
            context.update({'state': 'cancel'})
            self.with_context(context).add_stage_log()
            rec.write({'state': 'cancel',
                       # 'cancel_leave_user': self.env.user.name
                       })
            rec.get_approval_info()
            if rec.holiday_status_id.notif_leave_cancel:
                template_obj = self.env['mail.template']
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference(
                        'hr_holidays_extension',
                        'email_template_holidays_cancel')[1]
                except ValueError:
                    template_id = False
                if template_id and rec.holiday_status_id.notif_leave_refuse:
                    template_rec = template_obj.browse(template_id)
                    context = rec._set_email_template_context()
                    template_rec.with_context(context).send_mail(
                        rec.id, force_send=False)
            self._send_email(
                'hr_holidays_extension.email_template_holidays_cancel')
        return True

    def _check_state_access_right(self, vals):
        return True

    def _check_leave_validation(self, employee_id, date_from, date_to, holiday_status_id):
        holiday_obj = self.env['hr.holidays.public']
        ex_ph = holiday_status_id.ex_public_holidays
        rest_days = self._get_rest_days(employee_id)
        if rest_days:
            if date_from and date_from.weekday() in rest_days:
                raise Warning(_('Please, You are not allowed to select an '
                                'off day, For more information contact the HR '
                                'Team.'))
            if date_to and date_to.weekday() in rest_days:
                raise Warning(_('Please, You are not allowed to select an '
                                'off day, For more information contact the HR '
                                'Team.'))
        if date_from and (holiday_obj.is_public_holiday(date_from)) \
                and ex_ph:
            raise Warning(
                _('You can not start you'
                  ' leave from a public holiday,'
                  ' please choose another day.'))
        elif date_to and (holiday_obj.is_public_holiday(date_to)) and \
                ex_ph:
            raise Warning(
                _('You can not finished your'
                  ' leave on public holiday,'
                  ' please choose another day.'))
        if (date_from and date_to) and (date_from > date_to):
            raise Warning(
                _('The start date must be anterior to the end date.'))

        return True

    @api.multi
    def send_notify(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
        }

    def _get_permitted_leave_type(self, employee):
        holidays_status_obj = self.env['hr.holidays.status']
        holidays_status_id = []
        holidays_status_id_both_male_female = []
        holidays_status_id_both_religion = []
        holidays_status_rec = holidays_status_obj.search([
            ('is_gender', '=', False),
            ('is_religion', '=', False)
        ])

        if employee.religion == 'other':
            holidays_status_id_both_male_female = holidays_status_obj. \
                search([('religion', '=', 'o'),
                        ('is_gender', '=', False)])
        if employee.religion == 'muslim':
            holidays_status_id_both_male_female = holidays_status_obj. \
                search([('religion', '=', 'm'),
                        ('is_gender', '=', False)])
        if employee.gender == 'male':
            holidays_status_id_both_religion = holidays_status_obj. \
                search([('is_religion', '=', False),
                        ('is_gender', '=', True),
                        ('gender', '=', 'm')])
        if employee.gender == 'female':
            holidays_status_id_both_religion = holidays_status_obj. \
                search([('is_religion', '=', False),
                        ('is_gender', '=', True),
                        ('gender', '=', 'f')])

        if employee.gender == 'male':
            if employee.religion == 'muslim':
                holidays_status_id = holidays_status_obj. \
                    search([('is_religion', '=', True),
                            ('is_gender', '=', True),
                            ('gender', '=', 'm'),
                            ('religion', '=', 'm')])
            if employee.religion == 'other':
                holidays_status_id = holidays_status_obj. \
                    search([('is_religion', '=', True),
                            ('is_gender', '=', True),
                            ('gender', '=', 'm'),
                            ('religion', '=', 'o')])

        elif employee.gender == 'female':
            if employee.religion == 'muslim':
                holidays_status_id = holidays_status_obj. \
                    search([('is_religion', '=', True),
                            ('is_gender', '=', True),
                            ('gender', '=', 'f'),
                            ('religion', '=', 'm')])
            if employee.religion == 'other':
                holidays_status_id = holidays_status_obj. \
                    search([('is_religion', '=', True),
                            ('is_gender', '=', True),
                            ('gender', '=', 'f'),
                            ('religion', '=', 'o')])
        all_dic = []
        if holidays_status_id:
            all_dic += \
                holidays_status_id and \
                holidays_status_id.ids or []
        if holidays_status_rec:
            all_dic += \
                holidays_status_rec and \
                holidays_status_rec.ids or []
        if holidays_status_id_both_religion:
            all_dic += \
                holidays_status_id_both_religion and \
                holidays_status_id_both_religion.ids or []
        if holidays_status_id_both_male_female:
            all_dic += \
                holidays_status_id_both_male_female and \
                holidays_status_id_both_male_female.ids or []
        return all_dic

    def _get_hour_minute_from_shift(self, scheduled_hours):
        scheduled_hour = int(str(scheduled_hours).split(
            '.')[0])
        scheduled_minute = int(str(scheduled_hours).split(
            '.')[1])
        return scheduled_hour, scheduled_minute

    def _get_date_from_date_to_with_shift(self, shift_rec, date_from, date_to):
        if not shift_rec:
            raise Warning(_('You should have working schedule template in '
                            'contract or timeline. Kindly, Contact to HR '
                            'team.'))
        start_hour = shift_rec.default_scheduled_hours
        end_hour = 0.0
        for line in shift_rec.attendance_ids:
            if int(date_from.weekday()) == int(line.dayofweek):
                start_hour = line.hour_from
            if int(date_to.weekday()) == int(line.dayofweek):
                end_hour = line.hour_to
        if '.' in str(start_hour):
            on_hour, on_minute = self._get_hour_minute_from_shift(start_hour)
            date_from = date_from + relativedelta(hour=on_hour,
                                                  minute=on_minute)
        if end_hour:
            off_hour, off_minute = self._get_hour_minute_from_shift(end_hour)
            date_to = date_to + relativedelta(hour=off_hour,
                                              minute=off_minute)
        return date_from, date_to

    def _add_scheduled_hours(self, employee, dt, dt_to):
        shift_rec = self._get_shift_for_employee(employee)
        date_from, date_to = \
            self._get_date_from_date_to_with_shift(shift_rec, dt, dt_to)
        return date_from, date_to

    def _get_date(self, date_from, date_to):
        if date_to and not date_from:
            raise Warning(_('You should first select date from.'))
        if date_from > date_to:
            date_to = date_from
        dt, dt_to = False, False
        if date_from:
            dt = datetime.strptime(date_from, OE_DTFORMAT)
        if date_to:
            dt_to = datetime.strptime(date_to, OE_DTFORMAT)
        if dt and dt_to:
            dt, dt_to = self._add_scheduled_hours(self.employee_id, dt, dt_to)
        return dt, dt_to

    def _get_holidays_status_values(self, holiday_status_id):
        ex_rd, ex_ph = False, False
        if holiday_status_id:
            ex_rd = holiday_status_id.ex_rest_days
            ex_ph = holiday_status_id.ex_public_holidays
        return ex_rd, ex_ph

    def _get_number_of_days_values(self, dt, dt_to, employee):
        holiday_obj = self.env['hr.holidays.public']
        ex_rd, ex_ph = self._get_holidays_status_values(self.holiday_status_id)
        real_days_value, ph_days, r_days, working_days = 0, 0, 0, 0
        next_dt = dt
        rest_days = self._get_rest_days(employee)
        if (dt_to and dt) and (dt <= dt_to):
            td = dt_to - dt
            diff_day = td.days + float(td.seconds) / 86400
            number_of_days_temp = round(math.floor(diff_day)) + 1
        else:
            number_of_days_temp = 0
        count_days = number_of_days_temp
        while count_days > 0:
            public_holiday = holiday_obj.is_public_holiday(next_dt.date())
            rest_day = (next_dt.weekday() in rest_days and ex_rd)
            if public_holiday and ex_ph:
                ph_days += 1
            elif rest_day:
                r_days += 1
            else:
                working_days += 1
                real_days_value += 1
            next_dt += timedelta(days=+1)
            count_days -= 1
        return_date = False
        if dt_to:
            return_date = dt_to + timedelta(days=+1)
            while (return_date.weekday() in rest_days) or (
                    holiday_obj.is_public_holiday(return_date)):
                return_date = return_date + timedelta(days=+1)
            return_date = return_date.strftime('%B %d, %Y')
        total_days = working_days + ph_days + r_days
        return working_days, r_days, ph_days, real_days_value, total_days, \
               return_date

    def _get_proof(self, holiday_status_rec):
        proof_lst = []
        for line in holiday_status_rec.leave_type_proof_ids:
            proof_lst.append((0, 0, {'name': line.name, 'description':
                line.description, 'mandatory': line.mandatory}))
        return proof_lst

    def call_onchange_date(self):
        context = dict(self._context)
        if context.get('default_type') == 'remove':
            result = {'domain': {}}
            employee = self.employee_id
            nationality_id = employee.country_id.id
            all_dic = self._get_permitted_leave_type(employee)
            if self.holiday_status_id:
                if self.holiday_status_id.id not in all_dic:
                    self.holiday_status_id = []
            result['domain'].\
                update({'holiday_status_id': [('id', 'in', all_dic)]})
            holiday_status_rec = self.holiday_status_id
            dt, dt_to = self._get_date(self.date_from, self.date_to)
            self._check_leave_validation(
                self.employee_id, dt, dt_to, holiday_status_rec)
            # Compute and update the number of days
            working_days, r_days, ph_days, real_days_value, total_days, \
            return_date = self._get_number_of_days_values(dt, dt_to, employee)
            # Return Remaining Leaves
            vals = self._get_employee_balance(holiday_status_rec, employee)
            current_employee_balance = vals.get('current_employee_balance')
            flag_emp = False
            if holiday_status_rec:
                this_holiday_status_id = holiday_status_rec
                self.submit_message = this_holiday_status_id.submit_message
                self.about_leave_type = this_holiday_status_id.about_leave_type
                allow_trial_period = this_holiday_status_id.allow_trial_period
                if employee.contract_id.trial_date_end:
                    date_format = tools.DEFAULT_SERVER_DATE_FORMAT
                    date_traial = datetime.strptime(
                        employee.contract_id.trial_date_end, date_format)
                    today = datetime.today()
                    if date_traial >= today and not allow_trial_period:
                        raise Warning(
                            _('You cannot apply for this'
                              ' leave type while you are'
                              ' in the trial period.\n'
                              ' Please contact the HR department.'))

                flag_emp = this_holiday_status_id.alternative_emp_mandatory
            self.department_id = employee.department_id.id,
            self.working_days = working_days
            self.rest_days = r_days
            self.public_holiday_days = ph_days
            self.total_days = total_days
            self.return_date = return_date
            self.flag_emp_mandatory = flag_emp
            self.nationality_id = nationality_id
            self.date_from = dt
            self.date_to = dt_to
            self.max_allowed_days = current_employee_balance
            return result

    def _add_proof_required(self, holiday_status_rec):
        self.leave_proof_ids = [(5, 0, 0)]
        if self.proof_required:
            self.leave_proof_ids = self._get_proof(holiday_status_rec)

    @api.onchange(
        'date_to',
        'date_from',
        'employee_id')
    def onchange_date(self):
        """
        If there are no date set for date_to,
         automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        self.call_onchange_date()

    @api.onchange('holiday_status_id')
    def onchange_holidays_status(self):
        """
        If there are no date set for date_to,
         automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        context = dict(self._context)
        if context.get('default_type') == 'remove':
            self.call_onchange_date()
            # self.proof_required = self.holiday_status_id.proof_required
            if self.holiday_status_id:
                self.proof_required = self.holiday_status_id.proof_required
                self._add_proof_required(self.holiday_status_id)

    @api.model
    def default_get(self, fields_list):
        res = super(HrHolidays, self).default_get(fields_list)
        annual_leave_rec = self.env['hr.holidays.status'].search([('code', '=',
                                                                   'ANNLV')],
                                                                 limit=1)
        today_date = datetime.strftime(datetime.today(), OE_DTFORMAT)
        if res.get('type') == 'remove':
            res.update({'date_from': today_date, 'date_to': today_date})
            if annual_leave_rec:
                res.update({'holiday_status_id': annual_leave_rec.id})
        return res

    @api.multi
    def ceo_validate(self):
        for rec in self:
            rec.get_approval_info()
            rec.action_validate()
            rec.set_repeated_message()

    @api.multi
    def set_repeated_message(self):
        return self.write({'repeated_message': True})

    def get_approval_info(self):
        context = dict(self._context) or {}
        vals = {}
        new_vals = {
            'submit_user_id': False,
            'submit_date': False,
            'mngr_user_id': False,
            'mngr_approval_date': False,
            'hr_user_id': False,
            'hr_approval_date': False,
            'ceo_user_id': False,
            'ceo_approval_date': False,
            'refused_user_id': False,
            'refuse_date': False,
            'validate_approval_id': False,
            'validate_approval_date': False,
            'vp_user_id': False,
            'vp_approval_date': False,
        }
        if context.get('manager_approval'):
            vals.update({'mngr_user_id': self.env.user.id,
                         'mngr_approval_date': self._get_current_datetime()})
        elif context.get('vp_approval'):
            vals.update({'vp_user_id': self.env.user.id,
                         'vp_approval_date': self._get_current_datetime()})
        elif context.get('hr_approval'):
            vals.update({'hr_user_id': self.env.user.id,
                         'hr_approval_date': self._get_current_datetime()})
        elif context.get('ceo_approval'):
            vals.update({'ceo_user_id': self.env.user.id,
                         'ceo_approval_date': self._get_current_datetime()})
        elif context.get('submit_approval'):
            vals.update({'submit_user_id': self.env.user.id,
                         'submit_date': self._get_current_datetime()})
        elif context.get('refuse_approval'):
            vals.update(new_vals)
        elif context.get('cancel_approval'):
            vals.update(new_vals)
        elif context.get('amend_approval'):
            vals.update(new_vals)
            vals.update({'amend_by': self.env.user.id,
                         'amendment_date': self._get_current_datetime()})
        return self.write(vals)

    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def copy(self, default=None):
        if not self._check_group(
                'hr_holidays_extension.group_request_on_behalf_others'
        ):
            for rec in self:
                if rec.employee_id.user_id.id != self._uid:
                    raise Warning(_(
                        "You don't have the permissions to make such changes."
                    ))
        return super(HrHolidays, self).copy(default=default)

    def _call_approved(self):
        return self.action_validate()

    def _check_state_approval(self):
        holiday_status_rec = self.holiday_status_id
        if self.state == 'draft':
            if holiday_status_rec.double_validation:
                return self.action_confirm()
            elif holiday_status_rec.vp_approval:
                return self.confirm_mgt()
            elif holiday_status_rec.hr_appr:
                return self.action_approve()
            elif self.holiday_status_id.ceo_appr:
                return self.ceo_validate()
            else:
                return self.action_approve()
        elif self.state == 'confirm':
            if holiday_status_rec.vp_approval:
                return self.confirm_mgt()
            elif holiday_status_rec.hr_appr:
                return self.action_approve()
            elif self.holiday_status_id.ceo_appr:
                return self.ceo_validate()
            else:
                return self._call_approved()
        elif self.state == 'vp':
            if holiday_status_rec.hr_appr:
                return self.action_approve()
            elif self.holiday_status_id.ceo_appr:
                return self.ceo_validate()
            else:
                return self._call_approved()
        elif self.state == 'validate1':
            if self.holiday_status_id.ceo_appr:
                return self.ceo_validate()
            else:
                return self._call_approved()
        return True

    @api.multi
    def confirm_mgt(self):
        context = dict(self._context)
        for rec in self:
            if not self.env.user.has_group(
                    'hr_holidays_extension.group_leave_self_approval_srvs') \
                    and rec.employee_id.user_id.id == self.env.uid:
                raise UserError(_('You cannot approve your own request.'))
            if rec.holiday_status_id.vp_approval and rec.state != 'vp':
                rec.write({'state': 'vp'})
                rec._send_email('hr_holidays_extension.'
                                'email_template_holidays_update_vp')
                rec.with_context(context).get_approval_info()
            else:
                rec.get_approval_info()
                rec.set_repeated_message()
                rec._check_state_approval()

    @api.model
    def _get_locked_balance(self, employee_rec, preliminary_leave):
        """
        get locked balance
        :param employee_rec: employee record
        :param preliminary_leave: holiday status record
        :return:
        """
        locked_balance = 0.0
        holidays_rec = self.env['hr.holidays'].search([('state', 'not in',
                                                        ('draft', 'refuse',
                                                         'cancel', 'validate')
                                                        ), ('employee_id', '=',
                                                            employee_rec.id),
                                                       ('holiday_status_id',
                                                        '=',
                                                        preliminary_leave.id),
                                                       ('type', '=', 'remove')
                                                       ])
        for holiday in holidays_rec:
            if holiday.number_of_days_temp:
                locked_balance += holiday.number_of_days_temp
        return locked_balance

    @api.model
    def check_for_preliminary_leave(self, preliminary_leave, employee_rec):
        """
        check for preliminary leave.
        :param preliminary_leave: preliminary leave record
        :return:
        """
        future_balance_value = 0.0
        allow_future_balance = False
        remaining_balance = 0.0
        holiday_obj = self.env['hr.holidays']
        if preliminary_leave:
            remaining_leave_balance = preliminary_leave.get_days(
                employee_rec.id)
            if remaining_leave_balance:
                remaining_balance = remaining_leave_balance.get(
                    preliminary_leave.id).get('remaining_leaves')
                locked_balance = self._get_locked_balance(
                    employee_rec, preliminary_leave)
                remaining_balance = remaining_balance - locked_balance
            allow_future_balance = preliminary_leave.allow_future_balance
        if allow_future_balance:
            future_balance_value = \
                holiday_obj._calculate_emp_future_accrued_days(
                    employee_rec, self.date_from)
        leave_balance = remaining_balance + future_balance_value
        return leave_balance

    def _check_preliminary_leave(self, holiday_status_rec):
        if holiday_status_rec and \
                holiday_status_rec.preliminary_leave:
            leave_balance = self.check_for_preliminary_leave(
                holiday_status_rec.preliminary_leave,
                self.employee_id)
            if leave_balance > 1:
                p_leave = holiday_status_rec.preliminary_leave.name
                raise Warning(_('You are not allowed to request this'
                                ' kind of leave unless your %s balance'
                                ' less than 1.' % (p_leave)))
        return True

    def _check_employee_user(self, employee_rec):
        if not employee_rec:
            raise \
                Warning(_('You cannot send'
                          ' the request'
                          ' without selecting'
                          ' an employee'))
        if not employee_rec.leave_manager_id:
            raise Warning(_('To proceed, The employee should '
                            'be '
                            'linked '
                            'to his/her manager in the '
                            'system.'))
        if not employee_rec.leave_manager_id.user_id:
            raise Warning(_("To proceed, The employee's "
                            "manager should be "
                            "linked to a user."))
        return True

    @api.multi
    def action_confirm(self):
        today = datetime.today()
        for this in self:
            this._check_employee_user(this.employee_id)
            this._check_preliminary_leave(this.holiday_status_id)
            # check for leave
            contract_dic = this.emp_contract_id
            exception_bool = this.ex_leave
            this.get_approval_info()
            if exception_bool:
                if not self.skip_notifications:
                    this._send_email('hr_holidays_extension.'
                                     'email_template_holidays_update_mgt')
                return self.write({
                    'state': 'confirm',
                })
            date_format = tools.DEFAULT_SERVER_DATE_FORMAT
            if this.id:
                allow_trial_period = this.holiday_status_id.allow_trial_period
                if contract_dic.trial_date_end:
                    date_traial = datetime.strptime(
                        contract_dic.trial_date_end, date_format)
                    if date_traial >= today and not \
                            allow_trial_period and not exception_bool:
                        raise Warning(_('You cannot'
                                        ' apply for this'
                                        ' leave type while'
                                        ' you are in the trial'
                                        ' period.\n Please'
                                        ' contact the HR'
                                        ' department.'))
                if not self.skip_notifications:
                    this._send_email(
                        'hr_holidays_extension.'
                        'email_template_holidays_update_mgt')
                return self.write({'state': 'confirm'})
            else:
                raise Warning(_('You cannot send'
                                ' the request to'
                                ' manager without'
                                ' save the record '))

    @api.multi
    def action_validate(self):
        for holiday in self:
            if holiday.state == 'validate1' and not holiday.env.user.has_group(
                    'hr_holidays.group_hr_holidays_manager'):
                raise UserError(
                    _('Only an HR Manager can'
                      ' apply the second approval'
                      ' on leave requests.'))

            if not self.skip_notifications:
                holiday._send_email('hr_holidays_extension.'
                                    'email_template_holidays_update_emp')
            holiday.write({
                'state': 'validate',
                'final_approval_user_id': self.env.user.id,
                'final_approval_date': datetime.now().strftime(
                    OE_DTFORMAT),
            })
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                meeting_values = {
                    'name': holiday.display_name,
                    'categ_ids': [
                        (6, 0, [holiday.holiday_status_id.categ_id.id])]
                    if holiday.holiday_status_id.categ_id else [],
                    'duration': holiday.number_of_days_temp * HOURS_PER_DAY,
                    'description': holiday.notes,
                    'user_id': holiday.user_id.id,
                    'start': holiday.date_from,
                    'stop': holiday.date_to,
                    'allday': False,
                    'state': 'open',
                        'privacy': 'confidential'
                }
                # Add the partner_id (if exist) as an attendee
                if holiday.user_id and holiday.user_id.partner_id:
                    meeting_values['partner_ids'] = [
                        (4, holiday.user_id.partner_id.id)]

                meeting = self.env['calendar.event'].with_context(
                    no_mail_to_attendees=True).create(meeting_values)
                holiday._create_resource_leave()
                holiday.write({'meeting_id': meeting.id})
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                for employee in holiday.category_id.employee_ids:
                    values = {
                        'name': holiday.name,
                        'type': holiday.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': holiday.holiday_status_id.id,
                        'date_from': holiday.date_from,
                        'date_to': holiday.date_to,
                        'notes': holiday.notes,
                        'number_of_days_temp': holiday.number_of_days_temp,
                        'parent_id': holiday.id,
                        'employee_id': employee.id
                    }
                    leaves += self.with_context(
                        mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True

    @api.multi
    def to_validate2(self):
        for this in self:
            # this.check_current_balance()
            this.get_approval_info()
            if this.holiday_status_id.ceo_appr \
                    and this.holiday_status_id.ceo_number == 0:
                if this.holiday_status_id.ceo_appr \
                        and not this.skip_notifications:
                    this._send_email('hr_holidays_extension.'
                                     'email_template_holidays_update_ceo')
                return this.write({
                    'state': 'ceo'})
            if (this.holiday_status_id.ceo_number > 0 and this.
                    holiday_status_id.ceo_number <= this.real_days) \
                    and this.holiday_status_id.ceo_appr:
                if this.holiday_status_id.ceo_appr \
                        and not this.skip_notifications:
                    this._send_email('hr_holidays_extension.'
                                     'email_template_holidays_update_ceo')
                this.write({
                    'state': 'ceo'})
            else:
                if not self.skip_notifications:
                    this._send_email('hr_holidays_extension.'
                                     'email_template_holidays_update_emp')
                this.write({
                    'state': 'validate',
                    'final_approval_user_id': self.env.user.id,
                    'final_approval_date': datetime.now().strftime(
                        OE_DTFORMAT),
                })

    def _check_behalf_others(self):
        allow_behalf_req = self._check_group(
            'hr_holidays_extension.group_request_on_behalf_others')
        if not allow_behalf_req:
            employee_rec = self.env['hr.employee'] \
                .search([('user_id', '=', self._uid)], limit=1)
            if self.employee_id != employee_rec:
                raise Warning(_('You are not allowed to do this change on '
                                'behalf of others.'))
        return True

    @api.multi
    def holidays_to_manager(self):
        today = datetime.today()
        for this in self:
            if not this.employee_id:
                raise Warning(_('You cannot'
                                ' send the request'
                                ' without selecting'
                                ' an employee'))
            if this.type == 'add':
                return this.write({
                    'state': 'validate'})
            this._check_employee_user(this.employee_id)
            this._check_leave_validation(this.employee_id,
                                         datetime.strptime(this.date_from,
                                                           OE_DTFORMAT),
                                         datetime.strptime(this.date_to,
                                                           OE_DTFORMAT),
                                         this.holiday_status_id)
            this._check_behalf_others()
            this.check_leave_allocation()
            contract_dic = this.emp_contract_id
            exception_bool = this.ex_leave
            if exception_bool:
                if this.holiday_status_id.double_validation:
                    return this.action_confirm()
                if this.holiday_status_id.hr_appr:
                    return this.action_approve()
            date_format = tools.DEFAULT_SERVER_DATE_FORMAT
            if this.real_days == 0:
                raise Warning(
                    _('You cannot submit this request becuase of number of '
                      'days is 0. Kindly, contact the HR'
                      ' Team'))
            if this.id:
                allow_trial_period = this.holiday_status_id.allow_trial_period
                if contract_dic['trial_date_end']:
                    date_traial = datetime.strptime(
                        contract_dic['trial_date_end'], date_format)
                    if date_traial >= today and not \
                            allow_trial_period and not exception_bool:
                        raise Warning(_('You cannot apply'
                                        ' for this leave'
                                        ' type while you'
                                        ' are in the trial'
                                        ' period.\n Please'
                                        ' contact the'
                                        ' HR department.'))
                this._check_state_approval()
            else:
                raise Warning(
                    _('You cannot send the request'
                      ' to manager without save the Record '))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _('You cannot delete a leave which is not in draft state.'))
        return super(HrHolidays, self).unlink()

    def _get_emp_accrual_days(self, date_diff, daily_accrual_rate):
        return date_diff * daily_accrual_rate

    @api.multi
    def _calculate_emp_future_accrued_days(self, employee, date_from):
        if date_from:
            date_from = datetime.strptime(date_from, OE_DTFORMAT)
        if not date_from:
            date_from = datetime.today()
        year_start_date, year_end_date = self._get_year_start_last_date(
            date_from)
        date_diff = get_date_diff_days360(
            year_start_date + relativedelta(years=1), date_from)
        daily_accrual_rate = self._get_employee_daily_balance(employee)
        emp_future_accrued_days = self._get_emp_accrual_days(date_diff,
                                                           daily_accrual_rate)
        return emp_future_accrued_days

    @api.constrains('state', 'real_days')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != \
                    'employee' or holiday.type != \
                    'remove' or not holiday.employee_id \
                    or holiday.holiday_status_id.limit:
                continue
            leave_days = holiday.holiday_status_id.get_days(
                holiday.employee_id.id)
            if holiday.real_days > holiday.max_allowed_days:
                raise Warning(_('The available balance'
                                ' is not sufficient'
                                ' for this leave type.\n'
                                'Please verify also'
                                ' the leaves waiting'
                                ' for validation.'))
            elif leave_days \
                    and leave_days[holiday.holiday_status_id.id][
                        'remaining_leaves'] < 0 \
                    or leave_days[holiday.holiday_status_id.id][
                        'virtual_remaining_leaves'] < 0:
                raise ValidationError(_('The number of'
                                        ' remaining leaves is'
                                        ' not sufficient for'
                                        ' this leave type.\n'
                                        'Please verify also'
                                        ' the leaves waiting'
                                        ' for validation.'))
        return True


class LeaveProofDocuments(models.Model):
    _name = 'leave.proof.documents'

    name = fields.Char(string='Name')
    mandatory = fields.Boolean('Mandatory')
    description = fields.Text('Description')
    document = fields.Binary('Document')
    document_file_name = fields.Char('File Name')
    leave_id = fields.Many2one('hr.holidays', string='Leave')
