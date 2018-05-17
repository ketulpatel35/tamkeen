from odoo import api, models, fields, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

SERVICE_STATUS = [('draft', 'To Submit'),
                  ('mngr_approval', 'Manager Approval'),
                  ('vp_approval', 'VP Approval'),
                  ('hr_approval', 'HR Approval'),
                  ('budget_approval', 'Budget Approval'),
                  ('ceo_approval', 'CEO Approval'),
                  ('approved', 'Confirm'),
                  ('rejected', 'Rejected'),
                  ('closed', 'Closed'),
                  ('cancelled', 'Cancelled'),
                  ('locked', 'Locked')]


class ServicePanelWizard(models.Model):
    _inherit = 'certificate.of.completion'

    @api.depends('coc_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.coc_approval_policy_id.sla_period or False
            sla_period_unit = \
                rec.coc_approval_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.coc_submit_date:
                    coc_submit_date = datetime.strptime(rec.coc_submit_date,
                                                        OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        coc_submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('coc_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.coc_submit_date:
                coc_submit_date = datetime.strptime(rec.coc_submit_date,
                                                    OE_DTFORMAT)
                if rec.coc_final_approval_date:
                    coc_final_approval_date = datetime.strptime(
                        rec.coc_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(coc_final_approval_date,
                                         coc_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, coc_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.coc_waiting_time = waiting_time

    @api.model
    def _get_employee(self):
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id or False

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    coc_approval_policy_id = fields.Many2one('service.configuration.panel',
                                             string='Policy')
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', coc_approval_policy_id)]",
        copy=False)
    endorsement_coc_required = fields.Boolean(string='Endorsement Required',
                                              invisible=True)
    endorsement_coc_text = fields.Text(
        related='coc_approval_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True)
    endorsement_coc_approved = fields.Boolean(string='Endorsement Approved',
                                              track_visibility='onchange',
                                              readonly=1,
                                              states={'draft': [('readonly',
                                                                False)]})
    coc_submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.',
    )
    coc_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                      copy=False)
    coc_id = fields.Many2one('certificate.of.completion',
                             string='Certificate of Completion')
    state = fields.Selection(SERVICE_STATUS,
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             help='When the Coc is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded based on the service type '
                                  'configuration.',
                             default='draft')
    employee_id = fields. \
        Many2one('hr.employee',
                 string="Requester",
                 readonly=True, default=_get_employee, copy=False)
    coc_waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                                   string='Waiting Time',
                                   method=True, copy=False,
                                   states={'draft': [('readonly', False)]})

    coc_final_approval_date = fields.Datetime('Final Approval Date',
                                              readonly=True, copy=False)
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA',
        method=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]})
    coc_mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                       readonly=True, copy=False)
    coc_mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                             readonly=True, copy=False)
    coc_vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                     readonly=True, copy=False)
    coc_vp_approval_date = fields.Datetime(string='VP Approval Date',
                                           readonly=True, copy=False)
    coc_budget_user_id = fields.Many2one('res.users', string='Budget Approval',
                                         readonly=True, copy=False)
    coc_budget_approval_date = fields.Datetime(string='Budget Approval Date',
                                               readonly=True, copy=False)
    coc_hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                     readonly=True, copy=False)
    coc_hr_approval_date = fields.Datetime(string='HR Approval Date',
                                           readonly=True, copy=False,
                                           track_visibility='onchange')
    coc_final_approval_user_id = fields.Many2one('res.users',
                                                 string='Final Approval',
                                                 readonly=True, copy=False)
    coc_final_approval_date = fields.Datetime('Final Approval Date',
                                              readonly=True, copy=False)
    coc_service_log_ids = fields.One2many('service.log',
                                          'coc_request_id',
                                          string='Service Logs')
    coc_return_user_id = fields.Many2one('res.users', string='Return By',
                                         readonly=True, copy=False)
    coc_return_date = fields.Datetime(string='Return Date',
                                      readonly=True, copy=False)
    coc_rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                           readonly=True, copy=False)
    coc_rejected_date = fields.Datetime(string='Rejected Date',
                                        readonly=True, copy=False)
    coc_closed_user_id = fields.Many2one('res.users', string='Closed By',
                                         readonly=True, copy=False)
    coc_closed_date = fields.Datetime(string='Closed Date',
                                      track_visibility='onchange')
    coc_cancel_user_id = fields.Many2one('res.users', string='Cancel By',
                                         readonly=True, copy=False)
    coc_cancel_date = fields.Datetime(string='Cancel Date',
                                      readonly=True, copy=False)

    @api.multi
    def write(self, vals):
        """
        ovwride write method
        :param vals:
        :return:
        """
        if vals and vals.get('state'):
            # Update milestone
            if vals.get('state') == 'approved':
                self.update_milestone_completion()
        res = super(ServicePanelWizard, self).write(vals)
        return res

    def _get_coc_policy_id(self):
        if self.company_id and self.company_id.coc_policy_id:
            return self.company_id.coc_policy_id

    @api.onchange('company_id')
    def onchange_company_id(self):
        pre_request_id = self._get_coc_policy_id()
        if not pre_request_id:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the Certificate of Completion policy is '
                            'applied.'))
        self.coc_approval_policy_id = pre_request_id.id
        if self.coc_approval_policy_id and \
           self.coc_approval_policy_id.states_to_display_ids:
            self.stage_id = \
                self.coc_approval_policy_id.states_to_display_ids[0].id
        if self.coc_approval_policy_id:
            self.endorsement_coc_required = \
                self.coc_approval_policy_id.endorsement_required

    # New [Submit for Approval]
    @api.multi
    def action_submit_for_coc_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        for rec in self:
            if not rec.coc_approval_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the policy is applied.'))
        self._check_point_for_all_stage()

        # All Button Comman method

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_coc_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.coc_service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.coc_service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.coc_service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.coc_service_validate4()
        else:
            return False
        return True

    @api.multi
    def service_coc_submit_mngr(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
                # self._send_email('hr_overtime.overtime_pre_req_send_manager')
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
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.coc_approval_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.coc_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.coc_approval_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.coc_approval_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.coc_approval_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
        return req_approvals

    @api.multi
    def _check_coc_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def _check_coc_user_permissions(self, signal='approve'):
        for rec in self:
            if not rec._check_coc_group('certificate_of_completion.'
                                        'group_coc_self_approval_srvs'):
                if rec.state == 'mngr_approval' and \
                        rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(
                        _("Please, Make sure that you have the rights to %s "
                          "your own request.") %
                        (signal))
        return False

    @api.multi
    def _check_coc_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.coc_approval_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You cannot submit the request without attaching a '
                          'document.\n For attaching a document: press save '
                          'then attach a document.'))
            if service.coc_approval_policy_id.endorsement_required and not \
               service.endorsement_coc_approved:
                raise Warning(
                    _("Please, You should agree on the endorsement to proceed "
                      "with your request."))

    @api.multi
    def _get_coc_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        service_states.append('approved')  # to add the approved state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    def _get_coc_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_coc_related_stage_id(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "Stage ID not found, Please Configure Service Stages for "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'coc_submitted_by': self.env.user.id,
                           'coc_submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'coc_mngr_user_id': self.env.user.id,
                 'coc_mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'coc_vp_user_id': self.env.user.id,
                 'coc_vp_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state, 'coc_budget_user_id': self.env.user.id,
                 'coc_budget_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'coc_hr_user_id': self.env.user.id,
                 'coc_hr_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        if current_state == 'open':
            result.update(
                {'state': dest_state})
        if current_state == 'rejected':
            result.update(
                {'state': dest_state})
        if current_state == 'locked':
            result.update(
                {'state': dest_state})
        if current_state == 'cancelled':
            result.update(
                {'state': dest_state,
                 'cancel_date': self._get_current_datetime()})
        return result

    @api.multi
    def _get_coc_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'certificate.of.completion')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.multi
    def _send_email(self, template_xml_ref, email_to, dest_state, id,
                    service_provider):
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
                        data_pool, template_pool, email_to,
                        dest_state, service_provider)
                    if email_template_context:
                        context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        id, force_send=False)
            return True

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        if dest_state == 'vp_approval':
            self._send_email(
                'coc_configuration.coc_pre_req_send_to_vp',
                None, dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'coc_configuration.coc_request_send_manager',
                None, dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'budget_approval':
            self._send_email(
                'coc_configuration.coc_pre_req_send_to_budget',
                None, dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'hr_approval':
            self._send_email(
                'coc_configuration.coc_pre_req_send_to_hr', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'ceo_approval':
            self._send_email(
                'coc_configuration.coc_pre_req_send_to_ceo', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'approved':
            self._send_email(
                'coc_configuration.coc_pre_req_approved', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'rejected':
            self._send_email(
                'coc_configuration.email_template_coc_request_reject', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'cancelled':
            self._send_email(
                'coc_configuration.email_template_coc_request_cancelled', None,
                dest_state, self.id, 'certificate_of_completion')
        elif dest_state == 'draft':
            self._send_email(
                'coc_configuration.email_template_coc_request_draft', None,
                dest_state, self.id, 'certificate_of_completion')
        return True

    @api.multi
    def coc_service_validate1(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate2(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate3(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate4(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = self._get_coc_dest_state(service)
            if dest_state:
                self.write(
                    self._get_coc_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def coc_service_validate5(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'approved'
            final_approval = {
                'coc_final_approval_user_id': self.env.user.id,
                'coc_final_approval_date': self._get_current_datetime(),
                'open_user_id': self.env.user.id,
                'open_date': self._get_current_datetime(),
            }
            self.write(final_approval)
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate6(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'rejected'
            self.write({'coc_rejected_user_id': self.env.user.id,
                        'coc_rejected_date':
                            self._get_current_datetime()})
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate9(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'cancelled'
            self.write({'coc_cancel_user_id': self.env.user.id,
                        'coc_cancel_date':
                            self._get_current_datetime()})
            self.write(
                self._get_coc_approval_info(service,
                                            dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def coc_service_validate10(self):
        for service in self:
            self._check_coc_user_permissions('approve')
            self._check_coc_service_restrictions()
            dest_state = 'draft'
            self.write({
                'coc_submit_date': False,
                'coc_submitted_by': False,
                'coc_mngr_user_id': False,
                'coc_mngr_approval_date': False,
                'coc_vp_user_id': False,
                'coc_vp_approval_date': False,
                'coc_hr_user_id': False,
                'coc_hr_approval_date': False,
                'coc_budget_user_id': False,
                'coc_budget_approval_date': False,
                'coc_ceo_user_id': False,
                'coc_ceo_approval_date': False,
                'open_user_id': False,
                'open_date': False,
                'coc_closed_user_id': False,
                'coc_closed_date': False,
                'locked_user_id': False,
                'locked_date': False,
                'coc_rejected_user_id': False,
                'coc_rejected_date': False,
                'coc_cancel_user_id': False,
                'coc_cancel_date': False,
                'coc_expected_approval_date_as_sla': False,
                'coc_final_approval_date': False,
                'coc_final_approval_user_id': False,
                'coc_waiting_time': False,
            })
            self.write({'coc_return_user_id': self.env.user.id,
                        'coc_return_date':
                            self._get_current_datetime()})
            self.write(
                self._get_coc_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'certificate_of_completion.certificate_of_completion_action_view'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def _set_email_template_context(self, data_pool,
                                    template_pool, email_to, dest_state,
                                    service_provider):
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = self._get_related_window_action_id(data_pool,
                                                       dest_state,
                                                       service_provider)
        if action_id:
            display_link = True
        context.update({
            'email_to': email_to,
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'certificate.of.completion'
        })
        return context

    @api.multi
    def send_notify(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        # try:
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
            # 'context': ctx,
        }


class ServiceLog(models.Model):
    _inherit = 'service.log'

    coc_request_id = fields.Many2one('certificate.of.completion',
                                     string='Certificate of Completion '
                                            'Requests')


class ServiceLogWizard(models.TransientModel):
    _inherit = 'service.log.wizard'

    @api.multi
    def button_confirm(self):
        context = dict(self._context)
        service_log_rec = super(ServiceLogWizard, self).button_confirm()
        if service_log_rec and context.get('active_id') and context.get(
           'active_model'):
            active_model_obj = self.env[context.get('active_model', False)]
            active_id = context.get('active_id')
            active_rec = active_model_obj.browse(active_id)
            print context
            if str(context.get('active_model')) == 'certificate.of.completion':
                service_log_rec.write(
                    {'coc_request_id': active_rec.id})
            if str(context.get('active_model')) == 'certificate.of.completion':
                if context.get('trigger') and context.get(
                   'trigger') == 'Rejected':
                    active_rec.coc_service_validate6()
                if context.get('trigger') and context.get(
                   'trigger') == 'Locked':
                    active_rec.service_validate7()
                if context.get('trigger') and context.get(
                   'trigger') == 'Closed':
                    active_rec.service_validate8()
                if context.get('trigger') and \
                   context.get('trigger') == 'Cancelled':
                    active_rec.coc_service_validate9()
                if context.get('trigger') and context.get(
                   'trigger') == 'Returned':
                    active_rec.coc_service_validate10()
        return service_log_rec

    @api.onchange('coc_approval_policy_id')
    def onchange_coc_approval_policy_id(self):
        if self.coc_approval_policy_id and \
           self.coc_approval_policy_id.states_to_display_ids:
            self.stage_id = \
                self.coc_approval_policy_id.states_to_display_ids[0].id
