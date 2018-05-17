from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from dateutil.relativedelta import relativedelta

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class OrgEndOfService(models.Model):
    _name = 'org.end.of.service'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'End of Service'
    _order = 'name desc'

    SERVICE_STATUS = [('draft', 'To Submit'),
                      ('mngr_approval', 'Direct Manager'),
                      ('vp_approval', 'VP'),
                      ('hr_approval', 'HR Review'),
                      ('ceo_approval', 'CEO'),
                      ('final_hr_approval', 'HR Review'),
                      ('finance_processing', 'Finance Processing'),
                      ('approved', 'Confirm'),
                      ('rejected', 'Rejected')]

    @api.multi
    def _get_employee_name(self):
        """
        :return:
        """
        employee_rec = self.env['hr.employee'].search([
            ('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    @api.onchange('end_of_service_policy_id')
    def onchange_end_of_service_policy(self):
        """
        :return: onchange end of service.
        """
        if self.end_of_service_policy_id and \
                self.end_of_service_policy_id.states_to_display_ids:
            stage_rec = self.end_of_service_policy_id.states_to_display_ids[0]
            stage_list = filter(None, map(
                lambda x: x.case_default and x,
                self.end_of_service_policy_id.states_to_display_ids))
            if stage_list:
                stage_rec = stage_list[0]
            self.stage_id = stage_rec.id

    @api.depends('eos_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.eos_submit_date:
                eos_submit_date = datetime.strptime(
                    rec.eos_submit_date, OE_DTFORMAT)
                if rec.eos_final_approval_date:
                    eos_final_approval_date = datetime.strptime(
                        rec.eos_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(eos_final_approval_date,
                                         eos_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, eos_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.eos_waiting_time = waiting_time

    @api.depends('eos_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        """
        :return:
        """
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.end_of_service_policy_id.sla_period or False
            sla_period_unit = \
                rec.end_of_service_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.eos_submit_date:
                    eos_submit_date = datetime.strptime(
                        rec.eos_submit_date, OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        eos_submit_date + _intervalTypes[
                            sla_period_unit](sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('calendar_event_ids')
    def _compute_meeting_count(self):
        """
        count total meeting events
        :return:
        """
        for rec in self:
            rec.meeting_count = len(self.calendar_event_ids.ids)

    name = fields.Char(string="Request Number", readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee Name',
                                  default=_get_employee_name, copy=False)
    employee_company_id = fields.Char(string='Employee ID', readonly=True)
    job_id = fields.Many2one('hr.job', 'Position')
    department_id = fields.Many2one(
        'hr.department', string='Organization Unit', copy=False)
    org_unit_type = fields.Selection([
        ('root', 'Root'), ('business', 'Business Unit'),
        ('department', 'Department'), ('section', 'Section')],
        string='Organization Unit Type', copy=False)
    date_of_joining = fields.Date(
        string='Date of Joining', copy=False)
    nationality_id = fields.Many2one('res.country', string='Nationality',
                                     readonly=True,
                                     store=True)
    email = fields.Char('Work Email')
    mobile = fields.Char('Mobile Number')
    last_day_of_work = fields.Date('Last Day Of Work')
    request_type = fields.Many2one('org.end.of.service.type', 'Request Type')
    end_of_service_policy_id = fields.Many2one('service.configuration.panel',
                                               string='End of Service Policy')
    about_service = fields.Text(
        string='About The Service',
        related='end_of_service_policy_id.about_service')
    stage_id = fields.Many2one(
        'service.panel.displayed.states', string='States To Be Displayed',
        domain="[('service_type_ids', '=', end_of_service_policy_id)]",
        index=True, copy=False)
    state = fields.Selection(
        SERVICE_STATUS, string='Status', readonly=True,
        track_visibility='onchange',
        help='When the End of Service Request is created the status is '
             '\'Draft\'.\n Then the request will be forwarded based on the '
             'service type configuration.', default='draft')
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company')
    endorsement_text = fields.Text(
        related='end_of_service_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_required = fields.Boolean(
        string='Endorsement Approved',
        readonly=1, copy=False, states={'draft': [('readonly', False)]})
    endorsement_for_eos = fields.Boolean(
        related='end_of_service_policy_id.endorsement_required',
        store=True,
        string='Endorsement Required for End of Service')
    # approvals
    eos_submitted_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True, copy=False,
        help='Who requested the service.')
    eos_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                      copy=False)
    eos_manager_user_id = fields.Many2one(
        'res.users', string='Manager Approval', readonly=True, copy=False)
    eos_manager_approval_date = fields.Datetime(
        string='Manager Approval Date', readonly=True, copy=False)
    eos_vp_user_id = fields.Many2one(
        'res.users', string='VP Approval', readonly=True, copy=False)
    eos_vp_approval_date = fields.Datetime(
        string='VP Approval Date', readonly=True, copy=False)
    eos_hr_user_id = fields.Many2one(
        'res.users', string='HR Approval', readonly=True, copy=False)
    eos_hr_approval_date = fields.Datetime(
        string='HR Approval Date', readonly=True, copy=False)
    eos_ceo_user_id = fields.Many2one(
        'res.users', string='CEO Approval', readonly=True, copy=False)
    eos_ceo_approval_date = fields.Datetime(
        string='CEO Approval Date', readonly=True, copy=False)
    eos_final_hr_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    eos_final_hr_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    eos_finance_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    eos_finance_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    eos_rejected_user_id = fields.Many2one(
        'res.users', string='Rejected By', readonly=True, copy=False)
    eos_rejected_date = fields.Datetime(
        string='Rejected Date', readonly=True, copy=False)
    eos_final_approval_date = fields.Datetime(
        'Final Approval Date', readonly=True, copy=False)
    eos_waiting_time = fields.Char(
        compute=_calculate_ongoing_waiting_time,
        string='Waiting Time', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    service_log_ids = fields.One2many('service.log', 'end_of_service_id',
                                      'Service Logs')
    recommend_negotiation_ids = fields.One2many(
        'recommend.negotiation', 'end_of_service_id',
        string='Recommend Negotiation By')
    calendar_event_ids = fields.One2many(
        'calendar.event', 'end_of_service_id', 'Events')
    meeting_count = fields.Integer(
        '# Meetings', compute='_compute_meeting_count')
    survey_id = fields.Many2one(
        'survey.survey', 'Survey',
        related='end_of_service_policy_id.eos_survey_id')
    response_id = fields.Many2one('survey.user_input', "Response",
                                  ondelete="set null", oldname="response")

    @api.model
    def _get_end_of_service_policy(self):
        if not self.company_id or not self.company_id.end_of_service_policy_id:
            raise Warning(_('There is no an active policy for the end of '
                            'service, For more information, Kindly contact '
                            'the HR Team.'))
        return self.company_id.end_of_service_policy_id

    @api.onchange('company_id')
    def onchange_company_id(self):
        end_of_service_policy = self._get_end_of_service_policy()
        if not end_of_service_policy:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the enf of service policy has been '
                            'applied.'))
        self.end_of_service_policy_id = end_of_service_policy.id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        Onchange Employee Id
        :return:
        """
        if self.employee_id:
            self.email = self.employee_id.work_email
            self.mobile = self.employee_id.mobile_phone
            self.employee_company_id = self.employee_id.f_employee_no
            self.job_id = self.employee_id.job_id and \
                          self.employee_id.job_id or False
            self.department_id = self.employee_id.department_id and \
                                 self.employee_id.department_id.id or False
            self.org_unit_type = self.employee_id.department_id and \
                                 self.employee_id.department_id.org_unit_type
            self.date_of_joining = self.employee_id.initial_employment_date
            self.nationality_id = self.employee_id.country_id and \
                                  self.employee_id.country_id.id

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'org.end.of.service')
        res = super(OrgEndOfService, self).create(vals)
        return res

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if self.end_of_service_policy_id and \
                self.end_of_service_policy_id.states_to_display_ids:
            stage_rec = self.end_of_service_policy_id.states_to_display_ids[0]
            stage_list = filter(None, map(
                lambda x: x.case_default and x,
                self.end_of_service_policy_id.states_to_display_ids))
            if stage_list:
                stage_rec = stage_list[0]
            self.stage_id = stage_rec.id
        default.update({'stage_id': stage_rec.id})
        return super(OrgEndOfService, self).copy(default)

    # common methods for all buttons
    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.end_of_service_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.end_of_service_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.end_of_service_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.end_of_service_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
            if service.end_of_service_policy_id.hr_approval:
                req_approvals.append('final_hr_approval')
            if service.end_of_service_policy_id.finance_approval:
                req_approvals.append('finance_processing')
        return req_approvals

    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals:
                    return True
        return False

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.action_submit_to_manager()
        elif self.is_transition_allowed('vp_approval'):
            self.action_submit_to_vp_approval()
        elif self.is_transition_allowed('hr_approval'):
            self.action_submit_to_hr_approval()
        elif self.is_transition_allowed('ceo_approval'):
            self.action_submit_to_ceo_approval()
        elif self.is_transition_allowed('final_hr_approval'):
            self.action_submit_to_final_hr_approval()
        elif self.is_transition_allowed('finance_processing'):
            self.action_submit_to_finance_processing()
        else:
            return False
        return True

    @api.multi
    def _get_end_of_service_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        # service_states.append('finance_processing')  # to add the
        # service_states.append('waiting_repayment')
        service_states.append('approved')
        # approved state'
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    @api.multi
    def _check_end_of_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.end_of_service_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You are not allowed to submit the request without '
                          'attaching a document.\n For attaching a '
                          'document: press save then attach a document.'))
            if service.end_of_service_policy_id.endorsement_required and not \
                    service.endorsement_required:
                raise Warning(
                    _("To proceed, Kindly agree on the endorsement."))

    @api.model
    def _get_dest_related_stages(self, service, dest_state):
        """
        get destination stages
        :return:
        """
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'org.end.of.service')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.model
    def _get_end_of_service_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_dest_related_stages(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for %s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'eos_submitted_by': self.env.user.id,
                           'eos_submit_date': self._get_current_datetime()})
        elif current_state == 'mngr_approval':
            result.update(
                {'state': dest_state,
                 'eos_manager_user_id': self.env.user.id,
                 'eos_manager_approval_date': self._get_current_datetime()})
        elif current_state == 'vp_approval':
            result.update(
                {'state': dest_state,
                 'eos_vp_user_id': self.env.user.id,
                 'eos_vp_approval_date': self._get_current_datetime()})
        elif current_state == 'hr_approval':
            result.update(
                {'state': dest_state,
                 'eos_hr_user_id': self.env.user.id,
                 'eos_hr_approval_date': self._get_current_datetime()})
        elif current_state == 'ceo_approval':
            result.update(
                {'state': dest_state,
                 'eos_ceo_user_id': self.env.user.id,
                 'eos_ceo_approval_date': self._get_current_datetime()})
        elif current_state == 'final_hr_approval':
            result.update(
                {'state': dest_state,
                 'eos_final_hr_user_id': self.env.user.id,
                 'eos_final_hr_approval_date': self._get_current_datetime()})
        if current_state == 'finance_processing':
            result.update(
                {'state': dest_state,
                 'eos_finance_user_id': self.env.user.id,
                 'eos_finance_approval_date': self._get_current_datetime()})
        if current_state == 'rejected':
            result.update({'state': dest_state})
        return result

    # Buttons Actions
    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def action_submit_request(self):
        """
        submit end of service request
        :return:
        """
        for rec in self:
            if not rec.end_of_service_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the end of service policy has been applied.'))
            allow_behalf_req = rec._check_group(
                'org_end_of_service.group_eos_on_behalf_of_other')
            if not allow_behalf_req:
                employee_rec = self.env['hr.employee'].search(
                    [('user_id', '=', self._uid)], limit=1)
                if self.employee_id != employee_rec:
                    raise Warning(_('You are not allowed to do this change on '
                                    'behalf of others.'))
            rec._check_point_for_all_stage()

    @api.multi
    def action_submit_to_manager(self):
        for service in self:
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                service.write(
                    self._get_end_of_service_approval_info(
                        service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_vp_approval(self):
        """
        Manager Approval
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(
                    self._get_end_of_service_approval_info(service,
                                                           dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_approval(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(
                    self._get_end_of_service_approval_info(service,
                                                           dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_ceo_approval(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(
                    self._get_end_of_service_approval_info(service,
                                                           dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_final_hr_approval(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(
                    self._get_end_of_service_approval_info(service,
                                                           dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_finance_processing(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(
                    self._get_end_of_service_approval_info(service,
                                                           dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_finance_approved(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = self._get_end_of_service_dest_state(service)
            if dest_state:
                self.write(self._get_end_of_service_approval_info(
                    service, dest_state))
                self.write({
                    'eos_final_approval_date': self._get_current_datetime()
                })
                self._action_send_email(dest_state)
        return True

    @api.model
    def _get_return_dict(self):
        """
        return dictionary with
        :return:
        """
        return_dict = {
            'eos_submitted_by': False,
            'eos_submit_date': False,
            'eos_manager_user_id': False,
            'eos_manager_approval_date': False,
            'eos_vp_user_id': False,
            'eos_vp_approval_date': False,
            'eos_hr_user_id': False,
            'eos_hr_approval_date': False,
            'eos_ceo_user_id': False,
            'eos_ceo_approval_date': False,
            'eos_final_hr_user_id': False,
            'eos_final_hr_approval_date': False,
            'eos_finance_user_id': False,
            'eos_finance_approval_date': False,
            'eos_rejected_user_id': False,
            'eos_rejected_date': False,
            'eos_final_approval_date': False,
        }
        return return_dict

    @api.multi
    def action_end_of_service_return(self):
        """
        return end of service request
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_end_of_service_restrictions()
            dest_state = 'draft'
            result = self._get_end_of_service_approval_info(
                service, dest_state)
            result.update(self._get_return_dict())
            service.write(result)
            self._action_send_email('return_to_draft')
        return True

    @api.multi
    def action_schedule_meeting(self):
        """ Open meeting's calendar view to schedule meeting with employee.
            :return dict: dictionary value for created Meeting view
        """
        self.ensure_one()
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        partner_ids = self.env.user.partner_id.ids
        if self.eos_submitted_by.partner_id:
            partner_ids.append(self.eos_submitted_by.partner_id.id)
        action['context'] = {
            'search_default_end_of_service_id': self.id,
            'default_end_of_service_id': self.id,
            'default_partner_id': self.eos_submitted_by.partner_id.id,
            'default_partner_ids': partner_ids
        }
        return action

    @api.multi
    def action_start_survey(self):
        self.ensure_one()
        # create a response and link it to this employee
        if not self.response_id:
            response = self.env['survey.user_input'].create({
                'survey_id': self.survey_id.id,
                'partner_id': self.env.user.partner_id.id
            })
            self.response_id = response.id
        else:
            response = self.response_id
        # grab the token of the response and start surveying
        return self.survey_id.with_context(
            survey_token=response.token).action_start_survey()

    @api.multi
    def action_print_survey(self):
        """ If response is available then print this response otherwise
        print survey form (print template of the survey) """
        self.ensure_one()
        if not self.response_id:
            return self.survey_id.action_print_survey()
        else:
            response = self.response_id
            return self.survey_id.with_context(
                survey_token=response.token).action_print_survey()

    # Emails Related Methods
    @api.multi
    def send_notify(self):
        """
        This function opens a window to compose an email, with the edi sale
        template message loaded by default
        :return:
        """
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

    @api.multi
    def _get_related_window_action_id(self):
        data_pool = self.env['ir.model.data']
        window_action_id = False
        window_action_ref = \
            'org_end_of_service.org_end_of_service_action_view_all'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = data_pool.get_object_reference(
                addon_name, window_action_id)[1] or False
        return window_action_id

    @api.multi
    def _set_email_template_context(self, email_to):
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = self._get_related_window_action_id()
        if action_id:
            display_link = True
        context.update({
            'email_to': email_to,
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'org.end.of.service'
        })
        return context

    @api.multi
    def _send_email(self, template_xml_ref, email_to):
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
                    email_template_context = self._set_email_template_context(
                        email_to)
                    if email_template_context:
                        context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
        return True

    @api.multi
    def _action_send_email(self, dest_state):
        # context = dict(self._context)
        temp_xml_id = ''
        email_to = None
        if dest_state == 'mngr_approval':
            temp_xml_id = 'org_end_of_service.eos_request_send_to_manager'
        elif dest_state == 'vp_approval':
            temp_xml_id = 'org_end_of_service.eos_request_send_to_vp'
        elif dest_state == 'hr_approval':
            temp_xml_id = 'org_end_of_service.eos_request_send_to_hr_approval'
        elif dest_state == 'ceo_approval':
            temp_xml_id = 'org_end_of_service.eos_request_send_to_ceo'
        elif dest_state == 'final_hr_approval':
            temp_xml_id = \
                'org_end_of_service.eos_request_send_to_final_hr_approval'
        elif dest_state == 'finance_processing':
            temp_xml_id = 'org_end_of_service.' \
                          'eos_request_send_to_final_finance_processing'
        elif dest_state == 'approved':
            temp_xml_id = 'org_end_of_service.eos_request_approved'
        elif dest_state == 'return_to_draft':
            temp_xml_id = 'org_end_of_service.eos_request_return'
        # elif dest_state == '':
        #     temp_xml_id = 'org_end_   of_service.'

        if temp_xml_id:
            self._send_email(temp_xml_id, email_to)
        return True
