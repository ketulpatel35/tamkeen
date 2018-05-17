from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
import time

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

SERVICE_STATUS = [
    # ('new', 'To Submit'),
                  ('draft', 'To Submit'),
                  ('confirm', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  ('hr_approval', 'HR Approval'),
                  ('ceo_approval', 'CEO Approval'),
                  ('done', 'Approved'),
                  ('closed', 'Closed'),
                  ('rejected', 'Rejected'),
                  ('cancelled', 'Cancelled'),
                  # ('locked', 'Locked')
                  ]


class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    # Sending REMINDER Releted methods

    @api.one
    def _get_timesheet_dest_email_to(self):
        email_to = None
        current_state = self.state
        if current_state == 'confirm':
            email_to = self.employee_id.timesheet_manager_id.work_email
        elif current_state == 'vp_approval':
            email_to = self.employee_id.timesheet_vp_id.work_email
        elif current_state == 'hr_approval':
            email_to = self.timesheet_approval_policy_id.hr_email
        elif current_state == 'ceo_approval':
            email_to = self.employee_id.timesheet_ceo_id.work_email
        return email_to

    @api.multi
    def send_timesheet_reminder(self):
        # context = dict(context or {})
        # If there is no any linked reminder criteria,
        # the system will send a daily reminder.

        where_clause = [
            ('state', 'not in', ['draft', 'rejected','done']),
            ('timesheet_submit_date', '<',
             datetime.now().strftime('%Y-%m-%d 00:00:00'))
        ]
        time_requested_recs = self.search(where_clause)
        for time_req_rec in time_requested_recs:
            req_approvals = time_req_rec._get_service_req_approvals()
            if time_req_rec.state in req_approvals:
                # It may happen in case of changing the required approvals
                # before finalizing the pending, so it will be skipped.
                approval_delay_diff = \
                    time_req_rec._get_approval_delay(req_approvals)
                if time_req_rec.timesheet_approval_policy_id\
                        .approval_reminder_line:
                    delay_to_remind = time_req_rec.timesheet_approval_policy_id. \
                        approval_reminder_line.delay
                else:
                    # default take 1 day
                    delay_to_remind = 1
                if approval_delay_diff > \
                        delay_to_remind:
                    email_to = time_req_rec._get_timesheet_dest_email_to()
                    temp_id = 'timesheet_req_approval_reminder_cron_email_template'
                    time_req_rec._send_email(temp_id, email_to,
                                             time_req_rec.state,
                                             time_req_rec.id)
        return True

    @api.multi
    def _get_related_window_action_id(self, data_pool):
        window_action_id = False
        window_action_ref = \
            'hr_timesheet_sheet.act_hr_timesheet_sheet_my_timesheets'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _get_employee_name(self):
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    def _get_timesheet_policy_id(self):
        if self.company_id and self.company_id.timesheet_policy_id:
            if self.company_id.timesheet_policy_id.valid_from_date and \
                    self.company_id.timesheet_policy_id.valid_to_date:
                today_date = datetime.today().date()
                from_date = datetime.strptime(
                    self.company_id.timesheet_policy_id.valid_from_date,
                    OE_DATEFORMAT).date()
                to_date = datetime.strptime(
                    self.company_id.timesheet_policy_id.valid_to_date,
                    OE_DATEFORMAT).date()
                if from_date <= today_date <= to_date:
                    return self.company_id.timesheet_policy_id
                else:
                    Warning(_('There is no an active policy for the timesheet'
                                ', For more information, Kindly '
                                'contact the HR Team.'))
            else:
                raise Warning(_('There is no an active policy for the '
                                'timesheet'
                                ', For more information, Kindly '
                                'contact the HR Team.'))

    @api.multi
    def _send_email(self, template_xml_ref, email_to, id):
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url.static')
        if template_xml_ref:
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            template_id = data_pool.get_object_reference(
                'org_timesheet_extension', template_xml_ref)[1]
            action_id = self._get_related_window_action_id(data_pool)
            if action_id:
                display_link = True
            template_rec = template_pool.browse(template_id)
            if template_rec:
                context.update({
                    'email_to': email_to,
                    'base_url': base_url,
                    'display_link': display_link,
                    'action_id': action_id,
                    'model': 'loan.installments'
                })
                # if self._context and self._context.get('reason'):
                #     ctx.update({'reason': self._context.get('reason')})
                template_rec.with_context(context).\
                    send_mail(id, force_send=False)
            return True

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        context = dict(self._context)
        if dest_state == 'vp_approval':
            self._send_email('timesheet_request_send_manager', dest_state,
                             self.id)
        elif dest_state == 'confirm':
            self._send_email('timesheet_request_send_manager', dest_state,
                             self.id)
        elif dest_state == 'hr_approval':
            self._send_email('timesheet_pre_req_send_to_hr', dest_state,
                             self.id)
        elif dest_state == 'ceo_approval':
            self._send_email('timesheet_req_send_to_ceo', dest_state, self.id)
        elif dest_state == 'done':
            self._send_email('timesheet_req_approved', dest_state, self.id)
        elif dest_state == 'rejected':
            self.with_context(context)._send_email(
                'timesheet_req_rejected', dest_state, self.id)
        elif dest_state == 'closed':
            self.with_context(context)._send_email(
                'timesheet_req_closed', dest_state, self.id)
        elif dest_state == 'draft':
            self.with_context(context)._send_email(
                'email_template_timesheeet_draft', dest_state, self.id)
        return True

    @api.multi
    def _get_timesheet_dest_state(self):
        dest_state = ''
        current_state = self.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        service_states.append('done')
        # approved state'
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
                # if dest_state == 'confirm':
                #     dest_state = 'mngr_approval'
        return dest_state

    def _get_timesheet_approval_info(self, dest_state):
        current_state = self.state
        stage_id = self.get_timesheet_related_stage_id(dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for  "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state, 'timesheet_submitted_by':
                self.env.user.id,
                           'timesheet_submit_date':
                               self._get_current_datetime()})
        if current_state == 'confirm':
            result.update(
                {'state': dest_state, 'time_mngr_user_id': self.env.user.id,
                 'time_mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'time_vp_user_id': self.env.user.id,
                 'time_vp_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'time_hr_user_id': self.env.user.id,
                 'time_hr_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'time_ceo_user_id': self.env.user.id,
                 'time_ceo_approval_date': self._get_current_datetime(),
                 'time_final_approval_user_id': self.env.user.id,
                 'time_final_approval_date': self._get_current_datetime()})
        if current_state == 'done':
            result.update(
                {'state': dest_state})
        if current_state == 'closed':
            result.update(
                {'state': dest_state})
        if current_state == 'open':
            result.update(
                {'state': dest_state})
        if current_state == 'rejected':
            result.update(
                {'state': dest_state})
        return result
    
    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.timesheet_approval_policy_id.mngr_approval:
                req_approvals.append('confirm')
            if service.timesheet_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.timesheet_approval_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.timesheet_approval_policy_id.ceo_approval:
                    req_approvals.append('ceo_approval')
        return req_approvals

    @api.onchange('company_id')
    def onchange_company_id(self):
        timesheet_policy_id = self._get_timesheet_policy_id()
        if not timesheet_policy_id:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the timesheet policy has been '
                            'applied.'))
        if not  self.timesheet_approval_policy_id:
            self.timesheet_approval_policy_id = timesheet_policy_id.id

    # def _default_date_from(self):
    #     user = self.env['res.users'].browse(self.env.uid)
    #     r = user.company_id and user.company_id.timesheet_range or 'month'
    #     if r == 'month':
    #         return time.strftime('%Y-%m-01')
    #     elif r == 'week':
    #         return (
    #         datetime.today() + relativedelta(weekday=0, days=-6)).strftime(
    #             '%Y-%m-%d')
    #     elif r == 'year':
    #         return time.strftime('%Y-01-01')
    #     return fields.Date.context_today(self)

    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return time.strftime('%Y-%m-01')
        elif r == 'week':
            return (
            datetime.today() + relativedelta(weekday=0, days=-6)).strftime(
                '%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-01-01')
        return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1,
                                                     days=-1)).strftime(
                '%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=6)).strftime(
                '%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)

    @api.onchange('timesheet_approval_policy_id')
    def onchange_timesheet_approval_policy_id(self):
        if self.timesheet_approval_policy_id and \
                self.timesheet_approval_policy_id.states_to_display_ids:
            self.stage_id = \
                self.timesheet_approval_policy_id.states_to_display_ids[0].id

    @api.multi
    def get_timesheet_related_stage_id(self, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        if dest_state == 'confirm':
            dest_state = 'mngr_approval'
        if dest_state == 'done':
            dest_state = 'approved'
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'hr_timesheet_sheet.sheet')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.multi
    def action_submit_for_timesheet_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        for rec in self:
            if not rec.timesheet_approval_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the timesheet policy has been applied.'))
            employee_rec = self.env['hr.employee'] \
                .search([('user_id', '=', self._uid)], limit=1)
            if self.employee_id != employee_rec:
                raise Warning(_('You are not allowed to do this change on '
                                'behalf of others.'))
        self._check_point_for_all_stage()

    @api.multi
    def _check_timesheet_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.timesheet_approval_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You are not allowed to submit the request without '
                          'attaching a '
                          'document.\n For attaching a document: press save '
                          'then attach a document.'))
            if service.timesheet_approval_policy_id.endorsement_required and not \
                    service.endorsement_timesheet_approved:
                raise Warning(
                    _("To proceed, Kindly agree on the endorsement."))

    @api.multi
    def timesheet_service_validate1(self):
        for timesheet in self:
            dest_state = self._get_timesheet_dest_state()
            timesheet._check_timesheet_service_restrictions()
            if dest_state:
                timesheet.write(
                    timesheet._get_timesheet_approval_info(dest_state))
                timesheet.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def timesheet_service_validate2(self):
        for timesheet in self:
            dest_state = timesheet._get_timesheet_dest_state()
            timesheet._check_timesheet_service_restrictions()
            if dest_state:
                timesheet.write(
                    timesheet._get_timesheet_approval_info(dest_state))
                timesheet.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def timesheet_service_validate4(self):
        for timesheet in self:
            timesheet._check_timesheet_service_restrictions()
            dest_state = timesheet._get_timesheet_dest_state()
            if dest_state:
                timesheet.write(
                    timesheet._get_timesheet_approval_info(dest_state))
                timesheet.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def timesheet_service_validate5(self):
        """
        Business Owner Approval and submit for Procurement Second Review
        :return:
        """
        for timesheet in self:
            timesheet._check_timesheet_service_restrictions()
            dest_state = 'done'
            timesheet.write(self._get_timesheet_approval_info(dest_state))
            timesheet.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def timesheet_service_validate6(self):
        context = dict(self._context)
        for timesheet in self:
            timesheet._check_timesheet_service_restrictions()
            dest_state = 'rejected'
            timesheet.write({'time_rejected_user_id': self.env.user.id,
                        'time_rejected_date':
                            self._get_current_datetime()})
            timesheet.write(
                timesheet._get_timesheet_approval_info(dest_state))
            timesheet.with_context(context).check_dest_state_send_email(
                dest_state)
        return True

    @api.multi
    def timesheet_service_validate7(self):
        context = dict(self._context)
        for timesheet in self:
            timesheet._check_timesheet_service_restrictions()
            dest_state = 'draft'
            timesheet.write({'time_returned_user_id': self.env.user.id,
                             'time_returned_date':
                                 self._get_current_datetime()})
            timesheet.write(
                timesheet._get_timesheet_approval_info(dest_state))
            timesheet.with_context(context).check_dest_state_send_email(dest_state)
        return True

    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                        'accepted':
                    return True
        return False

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have t_get_loan_policy_ido check and run this code
        :return:
        """
        if self.is_transition_allowed('confirm'):
            self.service_timesheet_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.timesheet_service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.timesheet_service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.timesheet_service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.timesheet_service_validate4()
        else:
            return False
        return True

    @api.multi
    def service_timesheet_submit_mngr(self):
        for timesheet in self:
            dest_state = timesheet._get_timesheet_dest_state()
            timesheet._check_timesheet_service_restrictions()
            if dest_state:
                timesheet.write(
                    timesheet._get_timesheet_approval_info(dest_state))
                timesheet.check_dest_state_send_email(dest_state)
                # self._send_email('hr_overtime.overtime_pre_req_send_manager')
                return True

    @api.depends('timesheet_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.timesheet_approval_policy_id.sla_period or False
            sla_period_unit = \
                rec.timesheet_approval_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.timesheet_submit_date:
                    loan_submit_date = datetime.strptime(
                        rec.tiimesheet_submit_date, OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        loan_submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('time_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.timesheet_submit_date:
                timesheet_submit_date = datetime.strptime(rec.timesheet_submit_date,
                                                     OE_DTFORMAT)
                if rec.time_final_approval_date:
                    time_final_approval_date = datetime.strptime(
                        rec.time_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(time_final_approval_date,
                                         timesheet_submit_date)
                elif rec.state not in ['draft', 'rejected', 'done']:
                    diff = relativedelta(now, timesheet_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.time_waiting_time = waiting_time

    @api.multi
    def timesheet_closed(self):
        for rec in self:
            # dest_state = rec._get_timesheet_dest_state(rec)
            rec._check_timesheet_service_restrictions()
            dest_state = 'closed'
            if dest_state:
                self.write(
                    rec._get_timesheet_approval_info(dest_state))
                rec.check_dest_state_send_email(dest_state)
        return True

    employee_id = fields.Many2one('hr.employee', 'Employee Name',
                                  default=_get_employee_name,
                                  copy=False)
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee ID')
    job_id = fields.Many2one(related='employee_id.job_id',
                           string='Position')
    timesheet_type = fields.Selection([('salaried', 'Salaried Employees'),
                                       ('hourly', 'Hourly Employees')],
                                      related='employee_id.contract_id.timesheet_type',
                                      string='Timesheet Type')

    department_id = fields.Many2one('hr.department',
                                    related='job_id.department_id',
                                    string='Organization Unit', store=True)

    org_unit = fields.Selection([('root', 'Root'),
                                 ('business', 'Business Unit'),
                                 ('department', 'Department'), ('section',
                                                                'Section')],
                               related='department_id.org_unit_type',
                                string='Organization Unit Type')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company')
    timesheet_approval_policy_id = fields.Many2one(
        'service.configuration.panel', string='Timesheet Policy')

    # date_from = fields.Date(string='Date From', default=_default_date_from,
    #                         required=True,
    #                         index=True, readonly=True,
    #                         states={'draft': [('readonly', False)]})
    # date_to = fields.Date(string='Date To', default=_default_date_from,
    #                       required=True,
    #                       index=True, readonly=True,
    #                       states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', default=_default_date_from,
                            required=True,
                            index=True, readonly=True,
                            states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', default=_default_date_to,
                          required=True,
                          index=True, readonly=True,
                          states={'draft': [('readonly', False)]})
    # timesheet_line_ids = fields.One2many('sheet.time.recording.line',
    #                                      'sheet_id', string='Timesheet Lines')
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', timesheet_approval_policy_id)]",
        copy=False)
    state = fields.Selection(SERVICE_STATUS,
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             default='draft')
    endorsement_timesheet_required = fields.Boolean(string='Endorsement '
                                                         'Required',
                                               invisible=True)
    endorsement_timesheet_text = fields.Text(
        related='timesheet_approval_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_timesheet_approved = fields.Boolean(string='Endorsement Approved',
                                               track_visibility='onchange',
                                               readonly=1, copy=False,
                                               states={'draft': [('readonly',
                                                                  False)]})
    timesheet_submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.')
    timesheet_submit_date = fields.Datetime(string='Submit Date',
                                            readonly=True,
                                       copy=False)
    time_mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                        readonly=True, copy=False)
    time_mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                              readonly=True, copy=False)
    time_vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                      readonly=True, copy=False)
    time_vp_approval_date = fields.Datetime(string='VP Approval Date',
                                            readonly=True, copy=False)
    time_hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                      readonly=True, copy=False)
    time_hr_approval_date = fields.Datetime(string='HR Approval Date',
                                            readonly=True, copy=False,
                                            track_visibility='onchange')
    time_ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                      readonly=True, copy=False)
    time_ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                            readonly=True, copy=False,
                                            track_visibility='onchange')
    time_final_approval_date = fields.Datetime('Final Approval Date',
                                               readonly=True, copy=False)
    time_final_approval_user_id = fields.Many2one('res.users',
                                                  string='Final Approval',
                                                  readonly=True, copy=False)
    time_waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                                    string='Waiting Time',
                                    method=True, copy=False,
                                    states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA',
        method=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]})
    time_rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                            readonly=True, copy=False)
    time_rejected_date = fields.Datetime(string='Rejected Date',
                                         readonly=True, copy=False)
    time_returned_user_id = fields.Many2one('res.users', string='Returned By',
                                            readonly=True, copy=False)
    time_returned_date = fields.Datetime(string='Returned Date',
                                         readonly=True, copy=False)
    time_service_log_ids = fields.One2many('service.log',
                                           'time_request_id',
                                           string='Service Logs')

    @api.constrains('date_to', 'date_from', 'employee_id')
    def _check_sheet_date(self, forced_user_id=False):
        for sheet in self:
            new_user_id = forced_user_id or sheet.user_id and sheet.user_id.id
            if new_user_id:
                self.env.cr.execute('''
                        SELECT id
                        FROM hr_timesheet_sheet_sheet
                        WHERE (date_from <= %s and %s <= date_to)
                            AND user_id=%s
                            AND state not IN %s
                            AND id <> %s''',
                                    (sheet.date_to, sheet.date_from,
                                     new_user_id, tuple(['rejected',
                                                        'cancelled', 'draft']),
                                     sheet.id))
                if any(self.env.cr.fetchall()):
                    raise ValidationError(_(
                        'You cannot have 2 timesheets that overlap!\nPlease use the menu \'My Current Timesheet\' to avoid this problem.'))

    def _get_start_end_date(self, lock_day):
        today_date = date.today()
        end_date = today_date + relativedelta(day=lock_day, days=-1)
        start_date = end_date + relativedelta(months=-1, days=1)
        return start_date, end_date

    @api.multi
    def create_timesheet(self):
        return True
        # employee_obj = self.env['hr.employee']
        # employee_rec = employee_obj.search([('active', '=', True)])
        # unused_employee, domain = [], []
        # for employee in employee_rec:
        #     vals = {}
        #     if not employee.user_id or not employee.user_id.company_id:
        #         unused_employee.append(employee.name)
        #     vals.update({'employee_id': employee.id})
        #     lock_day = employee.user_id.company_id.payroll_lock_day
        #     if lock_day:
        #         start_date, end_date = self._get_start_end_date(lock_day)
        #         exist_timesheet_rec = self.search([('employee_id', '=',
        #                                        employee.id),
        #                      ('date_from', '=', start_date),
        #                      ('date_to', '=', end_date)])
        #         vals.update({'date_from': start_date, 'date_to': end_date})
        #         domain = [(
        #             'employee_id', '=', employee.id),
        #             ('date', '>=', start_date),
        #             ('date', '<=', end_date)]
        #         if not exist_timesheet_rec:
        #             timesheet_rec = self.create(vals)
        #         else:
        #             domain.append(('sheet_id', '=', False))
        #         recording_line_rec = self.env[
        #             'sheet.time.recording.line'].search(domain)
        #         for recording_line in recording_line_rec:
        #             recording_line.write({'sheet_id': timesheet_rec.id})
