from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DTFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from .overtime_pre_request import SERVICE_STATUS
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class HrOvertimeStatementRequest(models.Model):
    _name = 'overtime.statement.request'
    _description = 'Overtime Claim Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('overtime_claim_activity_ids.actual_hours')
    def _get_total_actual_hour(self):
        """
        compute total planed hours.
        :return:
        """
        actual_hours = 0
        for rec in self:
            for line in rec.overtime_claim_activity_ids:
                actual_hours += line.actual_hours
            rec.total_actual_hours = actual_hours

    @api.depends('overtime_claim_activity_ids.actual_day_cost')
    def _get_total_day_cost(self):
        """
        compute total planed hours.
        :return:
        """
        actual_day_cost = 0
        for rec in self:
            for line in rec.overtime_claim_activity_ids:
                actual_day_cost += line.actual_day_cost
            rec.total_day_cost = actual_day_cost

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals:
            seq = self.env['ir.sequence'].next_by_code('claim.overtime')
            vals.update({'name': seq})
        res = super(HrOvertimeStatementRequest, self).create(vals)
        return res

    @api.depends('final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), DTF)
            if rec.submit_date:
                submit_date = datetime.strptime(rec.submit_date, DTF)
                if rec.final_approval_date:
                    final_approval_date = datetime.strptime(
                        rec.final_approval_date, DTF)
                    diff = relativedelta(final_approval_date, submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.waiting_time = waiting_time

    @api.depends('submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.overtime_claim_policy_id.sla_period or False
            sla_period_unit = \
                rec.overtime_claim_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.submit_date:
                    submit_date = datetime.strptime(rec.submit_date,
                                                    DTF)
                    expected_approval_date_as_sla = \
                        submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('expected_approval_date_as_sla')
    def _get_color_code(self):
        """
        kanban card color changes based on expected approval date.
        :return:
        """
        for rec in self:
            if rec.expected_approval_date_as_sla:
                now = datetime.now()
                ex_date = datetime.strptime(
                    rec.expected_approval_date_as_sla, DTF)
                if now > ex_date:
                    rec.color = 7
                else:
                    rec.color = 0

    name = fields.Char('Reference', track_visibility='onchange')
    request_date = fields.Date('Request Date', default=datetime.today().date())
    employee_id = fields.Many2one(
        'hr.employee', states={'draft': [('readonly', False)]},
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self._uid)], limit=1) or False,
        string='Employee', readonly=1, track_visibility='onchange')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee Company ID')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Organization Unit',
                                    store=True)
    # Source document LINE
    pre_approval_request_id = fields.Many2one('overtime.pre.request',
                                              'Pre-Approved Request',
                                              track_visibility='onchange')
    overtime_claim_activity_ids = fields.One2many('overtime.claim.activity',
                                                  'overtime_claim_id',
                                                  'Overtime Claim',
                                                  track_visibility='onchange')
    # ot_hours = fields.Float('Pre Approved Hours',
    #                         compute='compute_overtime_total_hour',
    #                         track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    total_actual_hours = fields.Float(string='Total Actual Hours',
                                      compute='_get_total_actual_hour',
                                      store=True)
    total_day_cost = fields.Monetary(string='Total Day Cost',
                                     compute='_get_total_day_cost', store=True
                                     )
    cost_center_id = fields.Many2one('bs.costcentre',
                                     string='Cost Center',
                                     track_visibility='onchange')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          track_visibility='onchange',
                                          string="Analytic Account")
    is_verify = fields.Boolean(string='Verify Document',
                               track_visibility='onchange')
    waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                               string='Waiting Time',
                               method=True, copy=False,
                               states={'draft': [('readonly', False)]})
    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.',
    )
    submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                  copy=False,
                                  )
    mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                   readonly=True, copy=False,
                                   )
    mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                         readonly=True, copy=False,
                                         )
    vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                 readonly=True, copy=False,
                                 )
    vp_approval_date = fields.Datetime(string='VP Approval Date',
                                       readonly=True,
                                       copy=False,
                                       )
    ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                  readonly=True, copy=False,
                                  )
    ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                        readonly=True, copy=False,
                                        )
    budget_user_id = fields.Many2one('res.users', string='Budget Approval',
                                     readonly=True, copy=False,
                                     )
    budget_approval_date = fields.Datetime(string='Budget Approval Date',
                                           readonly=True, copy=False,
                                           )
    hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                 readonly=True, copy=False,
                                 )
    hr_approval_date = fields.Datetime(string='HR Approval Date',
                                       readonly=True,
                                       copy=False,
                                       )
    cancel_user_id = fields.Many2one('res.users', string='Cancelled By',
                                     readonly=True, copy=False,
                                     )
    cancel_date = fields.Datetime(string='Cancel Date',
                                  readonly=True, copy=False,
                                  )
    approved_user_id = fields.Many2one('res.users', string='Approved By',
                                       readonly=True, copy=False,
                                       )
    approved_date = fields.Datetime(string='Approved Date',
                                    readonly=True, copy=False,
                                    )

    locked_user_id = fields.Many2one('res.users', string='Locked By',
                                     readonly=True, copy=False,
                                     )
    locked_date = fields.Datetime(string='Locked Date', readonly=True,
                                  copy=False)
    closed_user_id = fields.Many2one('res.users', string='Closed By',
                                     readonly=True, copy=False,
                                     )
    closed_date = fields.Datetime(string='Closed Date',
                                  track_visibility='onchange')
    reset_user_id = fields.Many2one('res.users', string='Returned By',
                                    readonly=True, copy=False,
                                    )
    reset_date = fields.Datetime(string='Return Date',
                                 readonly=True, copy=False,
                                 )

    rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                       readonly=True, copy=False,
                                       )
    rejected_date = fields.Datetime(string='Rejected Date',
                                    readonly=True, copy=False,
                                    )
    final_approval_user_id = fields.Many2one('res.users', string='Final '
                                                                 'Approval',
                                             readonly=True, copy=False)

    final_approval_date = fields.Datetime('Final Approval Date',
                                          readonly=True, copy=False)
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company',
                                 )

    verify_attendance = fields.Boolean('Verify Attendance', copy=False)
    compute_overtime = fields.Boolean('Compute Overtime', copy=False)
    overtime_claim_policy_id = fields.Many2one('service.configuration.panel',
                                               string='Policy')
    about_service = fields.Text(
        string='About The Service',
        related='overtime_claim_policy_id.about_service',
        readonly=True,
        store=True)
    submit_message = fields.Text(
        related='overtime_claim_policy_id.submit_message',
        string='Submit Hint Message', store=True)
    overtime_pre_approval_type = fields.Selection(
        related='overtime_claim_policy_id.overtime_pre_approval_type',
        string='Policy', store=True)
    state = fields.Selection(SERVICE_STATUS, 'Status', readonly=True,
                             track_visibility='onchange',
                             help='When the request is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded based on the service type '
                                  'configuration.',
                             default='draft')
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA',
        method=True,
        store=True,
        copy=False,
        states={'draft': [('readonly', False)]})
    endorsement_required = fields.Boolean(string='Endorsement Required',
                                          invisible=True)
    endorsement_text = fields.Text(
        related='overtime_claim_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True)
    endorsement_approved = fields.Boolean(string='Endorsement Approved',
                                          track_visibility='onchange',
                                          readonly=1,
                                          states={
                                              'draft': [('readonly', False)]})
    file_to_fill = fields.Binary(
        related='overtime_claim_policy_id.file_to_fill',
        string='File To Fill',
        help="The required template that should be filled by the requester.",
        readonly=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]},
        store=True)
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', overtime_claim_policy_id)]",
        copy=False)
    service_log_ids = fields.One2many('service.log',
                                      'overtime_claim_request_id',
                                      string='Service Logs')
    consider_in_pre_request = fields.Boolean(string='Consider in Pre-Request')
    color = fields.Integer('Color', compute=_get_color_code)

    @api.multi
    def send_notify(self):
        """
        send notification
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
    def action_open_employee_form(self):
        """
        :return:
        """
        self.ensure_one()
        partners = self.employee_id.id | False
        view = self.env.ref(
            'hr.view_employee_form')
        return {
            'name': _('Employee'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee',
            'res_id': partners,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def default_get(self, fields_list):
        res = super(HrOvertimeStatementRequest, self).default_get(fields_list)
        if self._context.get('active_model') == 'overtime.pre.request':
            res.update({'pre_approval_request_id': self._context.get(
                'active_ids')})
        if self._context and self._context.get('cost_center'):
            res.update({'cost_center_id': self._context.get('cost_center')})
        return res

    def _check_policy(self):
        if not self.overtime_claim_policy_id:
            raise Warning(_('Need to configure Overtime Policy in Company!'))

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'hr_overtime.open_overtime_request_for_view_all'
        if dest_state == 'hr_approval':
            window_action_ref = \
                'hr_overtime.open_overtime_request_for_hr'
        if dest_state in ['mngr_approval', 'vp_approval', 'ceo_approval']:
            window_action_ref = \
                'hr_overtime.open_overtime_mngr_request_approval'
        if dest_state == 'budget_approval':
            window_action_ref = \
                'hr_overtime.open_overtime_request_for_budget'
        if dest_state in ['cancelled', 'locked', 'open', 'rejected', 'closed']:
            window_action_ref = \
                'hr_overtime.open_overtime_request_ess_requests'
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
            'model': 'overtime.claim.statement'
        })
        return context

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
                    if context.get('reason'):
                        context.update({'reason': context.get('reason')})
                    template_rec.with_context(context).send_mail(
                        id, force_send=False)
            return True

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        context = dict(self._context)
        if dest_state == 'vp_approval':
            self._send_email(
                'hr_overtime.overtime_request_send_to_vp',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'hr_overtime.overtime_request_send_to_manager',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'budget_approval':
            self._send_email(
                'hr_overtime.overtime_request_send_to_budget',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'hr_approval':
            self._send_email(
                'hr_overtime.overtime_claim_send_to_hr', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'ceo_approval':
            self._send_email(
                'hr_overtime.overtime_request_send_to_ceo', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'approved':
            self._send_email(
                'hr_overtime.overtime_request_approved', None,
                dest_state, self.id, 'overtime_pre_request')
            self._send_email(
                'hr_overtime.hr_overtime_request_approved', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'rejected':
            self.with_context(context)._send_email(
                'hr_overtime.email_template_overtime_request_reject', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'locked':
            self._send_email(
                'hr_overtime.email_template_overtime_locked', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'closed':
            self._send_email(
                'hr_overtime.email_template_overtime_request_closed', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'cancelled':
            self._send_email(
                'hr_overtime.email_template_overtime_request_cancel', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'daft':
            self._send_email(
                'hr_overtime.email_template_overtime_draft', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'payroll_processing':
            self._send_email(
                'hr_overtime.email_template_payroll_processing', None,
                dest_state, self.id, 'overtime_pre_request')
            self._send_email(
                'hr_overtime.hr_email_template_payroll_processing', None,
                dest_state, self.id, 'overtime_pre_request')
        return True

    @api.multi
    def generate_pyaslip_amendment(self):
        for rec in self:
            rec._check_policy()
            amendment_wizard_form = self.env.ref(
                'hr_overtime.generate_payslip_amendment_view', False)
            return {
                'name': _('Generate Payslip Amendment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'generate.payslip.amendment',
                'views': [(amendment_wizard_form.id, 'form')],
                'view_id': amendment_wizard_form.id,
                'target': 'new',
            }

    @api.multi
    def get_overtime_request(self):
        for rec in self:
            overtime_claim_request_list = []
            if rec.pre_approval_request_id:
                rec.overtime_claim_activity_ids.unlink()
                for line in rec.pre_approval_request_id.plan_activity_ids:
                    overtime_claim_request_list.append((0, 0, {
                        'date': line.date,
                        'activity_planned': line.activity_planned,
                        'expected_hours': (line.expected_hours -
                                           line.approved_hours),
                        'remark': line.remark,
                        'remaining_hours': (line.expected_hours -
                                            line.approved_hours)
                    }))
            rec.write({
                'overtime_claim_activity_ids': overtime_claim_request_list})

    @api.multi
    def reset_claim_lines(self):
        for rec in self:
            for line in rec.overtime_claim_activity_ids:
                line.unlink()
        return True

    def _get_current_datetime(self):
        return datetime.now().strftime(DTF)

    def _get_claim_request_policy_id(self):
        if self.company_id and self.company_id.overtime_policy_id:
            if self.company_id.overtime_policy_id.valid_from_date and \
                    self.company_id.overtime_policy_id.valid_to_date and \
                    self.company_id.overtime_policy_id:
                today_date = datetime.today().date()
                from_date = datetime.strptime(
                    self.company_id.overtime_policy_id.valid_from_date,
                    OE_DTFORMAT).date()
                to_date = datetime.strptime(
                    self.company_id.overtime_policy_id.valid_to_date,
                    OE_DTFORMAT).date()
                if from_date <= today_date <= to_date:
                    return self.company_id.overtime_policy_id
                else:
                    Warning(_('There is no an active policy for the Overtime'
                              ', For more information, Kindly '
                              'contact the HR Team.'))
            else:
                raise Warning(_('There is no an active policy for the Overtime'
                                ', For more information, Kindly '
                                'contact the HR Team.'))

    @api.onchange('company_id')
    def onchange_company_id(self):
        overtime_policy_id = self._get_claim_request_policy_id()
        if not overtime_policy_id:
            raise Warning(
                _('You are not allowed to apply for this request '
                  'until the policy is applied.'))
        self.overtime_claim_policy_id = overtime_policy_id.id

    @api.onchange('overtime_claim_policy_id')
    def onchange_overtime_claim_policy_id(self):
        if self.overtime_claim_policy_id:
            if self.overtime_claim_policy_id.states_to_display_ids:
                self.stage_id = \
                    self.overtime_claim_policy_id.states_to_display_ids[0].id
            self.endorsement_required = \
                self.overtime_claim_policy_id.endorsement_required
            self.verify_attendance = \
                self.overtime_claim_policy_id.hr_attendance_verification

    @api.multi
    def get_payslip_amendment(self):
        self.ensure_one()
        context = dict(self._context)
        # ir_model_obj = self.env['ir.model']
        # model_rec = ir_model_obj.search([('model', '=',
        #                                   'hr.payslip.amendment')])
        # if model_rec:
        #     context.update({'default_model_id': model_rec.id})
        # else:
        #     raise Warning(_('There are no Payslip Amendment Form.'))
        # context.update({'search_default_overtime_request_id': self.id})
        return {
            'name': 'Overtime Payslip Amendments',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip.amendment',
            'target': 'current',
            'context': context,
            'domain': [('overtime_request_id', 'in', self.ids)]
        }

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.overtime_claim_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.overtime_claim_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.overtime_claim_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.overtime_claim_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.overtime_claim_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
        return req_approvals

    @api.multi
    def _get_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'overtime.statement.request')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                   'accepted':
                    return True
        return False

    def _get_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_related_stage_id(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "Stage ID not found, Please Configure Service Stages for "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'submitted_by': self.env.user.id,
                           'submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'mngr_user_id': self.env.user.id,
                 'mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'vp_user_id': self.env.user.id,
                 'vp_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'hr_user_id': self.env.user.id,
                 'hr_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state, 'budget_user_id': self.env.user.id,
                 'budget_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        if current_state == 'approved':
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
                {'state': dest_state})
        if dest_state == 'approved' and not self.consider_in_pre_request:
            self.get_total_cost_hours()
        if current_state == 'payroll_processing':
            result.update(
                {'state': dest_state})
        return result

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_submit_mngr()
        elif self.is_transition_allowed('hr_approval'):
            self.service_validate3()
        elif self.is_transition_allowed('vp_approval'):
            self.service_validate2()
        elif self.is_transition_allowed('budget_approval'):
            self.service_validate4()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate5()
        else:
            return False
        return True

    def _get_month_first_last_date(self, date):
        add_month = date + relativedelta(months=1, day=1)
        last_date_s = add_month - relativedelta(days=1)
        first_date_s = last_date_s + relativedelta(day=1)
        return first_date_s, last_date_s

    def _get_year_first_last_date(self, date):
        first_date_s = date + relativedelta(month=1, day=1)
        last_date_s = date + relativedelta(month=12, day=31)
        return first_date_s, last_date_s

    def _get_maximum_monthly_hours(self, overtime_claim_policy_id):
        if overtime_claim_policy_id:
            maximum_hours_per_month = \
                overtime_claim_policy_id.maximum_hours_per_month
            return maximum_hours_per_month

    def _get_maximum_yearly_hours(self, overtime_claim_policy_id):
        if overtime_claim_policy_id:
            maximum_hours_per_year = \
                overtime_claim_policy_id.maximum_hours_per_year
            return maximum_hours_per_year

    def _get_maximum_day_hours(self, overtime_claim_policy_id):
        line_type = []
        for line in overtime_claim_policy_id.overtime_calculation_line_ids:
            line_type.append(line.type)
            if line.type == 'daily':
                maximum_hours_per_day = line.maximum_hour
                type = 'Daily'
                return maximum_hours_per_day, type
        if str('daily') not in line_type:
            raise Warning(_('No maximum daily configuration is set. '
                            'Please contact HR to proceed your request.'))

    def _get_maximum_rest_days(self, overtime_claim_policy_id):
        line_type = []
        for line in overtime_claim_policy_id.overtime_calculation_line_ids:
            line_type.append(line.type)
            if line.type == 'rest_day':
                type = 'Rest Day'
                maximum_hours_per_rest_day = line.maximum_hour
                return maximum_hours_per_rest_day, type
        if str('rest_day') not in line_type:
            raise Warning(_('No maximum rest days configuration is set.'
                            'Please contact HR to proceed your request.'))

    def _get_maximum_public_holidays(self, overtime_claim_policy_id):
        line_type = []
        for line in overtime_claim_policy_id.overtime_calculation_line_ids:
            line_type.append(line.type)
            if line.type == 'public_holiday':
                type = 'Public Holiday'
                maximum_hours_per_public_holiday = line.maximum_hour
                return maximum_hours_per_public_holiday, type
        if str('public_holiday') not in line_type:
            raise Warning(_('No maximum public holidays configuration is '
                            'set.'
                            'Please contact HR to proceed your request.'))

    def _get_planned_activity(self, first_date, last_date, employee_id):
        overtime_planned_activity_rec = self.env[
            'overtime.claim.activity']. \
            search([('date', '>=', first_date),
                    ('date', '<=', last_date),
                    ('overtime_claim_id.employee_id', '=', employee_id)])
        return overtime_planned_activity_rec

    # def _get_rest_days(self):
    #     rest_days = self.employee_id.contract_id. \
    #         working_hours.get_rest_days()
    #     return rest_days

    def _get_rest_days(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    def _check_day_maximum_hours(self, first_date, last_date,
                                 overtime_claim_policy_id,
                                 employee_id, actual_hours_line):
        actual_hours = 0.0
        public_holiday_obj = self.env['hr.holidays.public']
        if len(overtime_claim_policy_id.overtime_calculation_line_ids) >= 1:
            if first_date.weekday() in self._get_rest_days(
                    self.env['hr.employee'].browse(employee_id)):
                maximum_hours, type = self._get_maximum_rest_days(
                    overtime_claim_policy_id)
            elif public_holiday_obj.is_public_holiday(first_date):
                maximum_hours, type = self._get_maximum_public_holidays(
                    overtime_claim_policy_id)
            else:
                maximum_hours, type = self._get_maximum_day_hours(
                    overtime_claim_policy_id)
            overtime_planned_activity_rec = self._get_planned_activity(
                first_date, last_date, employee_id)
            for planned_activity in overtime_planned_activity_rec:
                actual_hours += planned_activity.actual_hours
            if actual_hours_line:
                actual_hours += actual_hours_line
        else:
            raise Warning(_('There are no configuration for overtime in '
                            'policy. For more information contact to HR.'))

    def _check_month_maximum_hours(self, first_date, last_date,
                                   overtime_claim_policy_id, employee_id,
                                   actual_hours_line):
        actual_hours = 0.0
        maximum_hours_per_month = self._get_maximum_monthly_hours(
            overtime_claim_policy_id)
        overtime_planned_activity_rec = self._get_planned_activity(first_date,
                                                                   last_date,
                                                                   employee_id)
        for planned_activity in overtime_planned_activity_rec:
            actual_hours += planned_activity.actual_hours
        if actual_hours_line:
            actual_hours += actual_hours_line
        if actual_hours > maximum_hours_per_month:
            raise Warning(_('You are not allowed to request more than %s '
                            'hour/s per month.') % maximum_hours_per_month)

    def _check_year_maximum_hours(self, first_date, last_date,
                                  overtime_claim_policy_id, employee_id,
                                  actual_hours_line):
        actual_hours = 0.0
        maximum_hours_per_year = self._get_maximum_yearly_hours(
            overtime_claim_policy_id)
        overtime_planned_activity_rec = self._get_planned_activity(first_date,
                                                                   last_date,
                                                                   employee_id)
        for planned_activity in overtime_planned_activity_rec:
            actual_hours += planned_activity.actual_hours
        if actual_hours_line:
            actual_hours += actual_hours_line
        if actual_hours > maximum_hours_per_year:
            raise Warning(_('You are not allowed to request more than %s '
                            'hour/s per year.') % maximum_hours_per_year)

    def check_maximum_hours(self, overtime_claim_policy_id):
        if not self.overtime_claim_activity_ids:
            raise Warning(_('You should have at least one planned activity.'))
        for line in self.overtime_claim_activity_ids:
            if line.date:
                date = datetime.strptime(line.date, OE_DTFORMAT)
                first_date, last_date = self._get_month_first_last_date(date)
                year_first_date, year_last_date = \
                    self._get_year_first_last_date(date)
                employee_id = self.employee_id.id
                self._check_day_maximum_hours(date, date,
                                              overtime_claim_policy_id,
                                              employee_id, False)
                self._check_month_maximum_hours(first_date, last_date,
                                                overtime_claim_policy_id,
                                                employee_id,
                                                False)
                self._check_year_maximum_hours(year_first_date, year_last_date,
                                               overtime_claim_policy_id,
                                               employee_id,
                                               False)

    @api.multi
    def check_overtime_request(self):
        # check Overtime pre-request lines date
        date_lst = []
        claim_date_str, claim_exp_0 = '', ''
        if self.pre_approval_request_id:
            for line in self.pre_approval_request_id.plan_activity_ids:
                date_lst.append(line.date)
            for claim_line in self.overtime_claim_activity_ids:
                if claim_line.expected_hours <= 0:
                    claim_exp_0 += str(claim_line.date) + ', '
                if claim_line.date not in date_lst:
                    claim_date_str += str(claim_line.date) + ', '
            if claim_date_str:
                raise Warning(_('There is no pre-request for the dates %s. '
                                'Please create a Pre-request for the dates '
                                '%s to proceed') % (claim_date_str,
                                                    claim_date_str))
            if claim_exp_0:
                raise Warning(_('The actual hours on %s are more than the '
                                'expected hours. Please create a new '
                                'pre-request '
                                'to continue the claim.') % (claim_exp_0,))

    @api.multi
    def unlink(self):
        for overtime in self:
            if overtime.state != 'draft':
                raise ValidationError(_('You can only delete '
                                        'the draft requests!'))
        return super(HrOvertimeStatementRequest, self).unlink()

    @api.multi
    def check_statement_request_check_actual_hours(self):
        for rec in self:
            actual_hours_date, actual_hours_0 = '', ''
            for line in rec.overtime_claim_activity_ids:
                if line.expected_hours and line.expected_hours < \
                   line.actual_hours:
                    actual_hours_date += str(line.date) + ', '
                if line.actual_hours <= 0:
                    actual_hours_0 += str(line.date)
            if actual_hours_date and rec.pre_approval_request_id:
                raise Warning(_("The actual hours shouldn't exceed "
                                "the expected hours for these dates"
                                " %s.") % actual_hours_date)
            if actual_hours_0:
                raise Warning(_("The actual hours should be more "
                                "than 0 for %s.") % actual_hours_0)

    @api.multi
    def check_repeated_date(self):
        date_list = []
        date_check_list = []
        for rec in self:
            for line in rec.overtime_claim_activity_ids:
                date_list.append(str(line.date))
            for date_lst in date_list:
                if date_lst not in date_check_list:
                    date_check_list.append(date_lst)
                else:
                    raise Warning(_(
                        "Kindly, Don't use the same date more "
                        "than one time."))

    # New [Submit for Approval]
    @api.multi
    def action_submit_for_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        # for rec in self:
        #     rec.check_maximum_hours(rec.overtime_claim_policy_id)
        for rec in self:
            if not rec.overtime_claim_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the policy is applied.'))
            rec.check_repeated_date()
            rec.check_statement_request_check_actual_hours()
            rec.check_overtime_request()
            rec.check_maximum_hours(rec.overtime_claim_policy_id)
        self._check_point_for_all_stage()

    @api.multi
    def get_total_cost_hours(self):
        for rec in self:
            if rec.pre_approval_request_id:
                for line in rec.pre_approval_request_id.plan_activity_ids:
                    for claim_line in rec.overtime_claim_activity_ids:
                        if line.date == claim_line.date:
                            line.approved_hours += claim_line.actual_hours
                            # rec.pre_approval_request_
                            # id.total_taken_hours += \
                            #     rec.total_actual_hours
                            # rec.pre_approval_request_id.
                            # taken_total_cost += \
                            #     rec.total_day_cost
                            # rec.consider_in_pre_request = True
        return True

    @api.multi
    def service_validate1(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def service_validate2(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.model
    def get_attendance_hour(self, employee_rec, date):
        """
        :param employee_rec:
        :param date:
        :return: attendance worked hour integer
        """
        att_hr = 0.00
        att_rec = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_rec.id),
            ('date', '=', date)])
        if att_rec:
            att_hr = int(att_rec.worked_hours)
        return att_hr

    @api.model
    def convert_in_time(self, hours):
        """
        time converter
        :param hours:
        :return:
        """
        minutes = hours * 60
        hours, minutes = divmod(minutes, 60)
        return hours, round(minutes, 2)

    @api.multi
    def attendance_verify(self):
        """
        hr verify attendance
        :return:
        """
        for ot_line_rec in self.overtime_claim_activity_ids:
            att_hr = self.get_attendance_hour(
                self.employee_id, ot_line_rec.date)
            con_att_h, con_att_m = self.convert_in_time(att_hr)
            worked_hours = "%02d.%02d" % (con_att_h, con_att_m)
            ot_line_rec.attendance_hours = worked_hours
        self.verify_attendance = False

    @api.multi
    def service_validate3(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def service_validate4(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def service_validate5(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def service_validate6(self):
        context = dict(self._context)
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'rejected'
            self.write({'rejected_user_id': self.env.user.id,
                        'rejected_date': self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.with_context(context).check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate7(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'locked'
            self.write({'locked_user_id': self.env.user.id,
                        'locked_date': self._get_current_datetime()})
            self.write(self._get_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate8(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'closed'
            self.write({'closed_user_id': self.env.user.id,
                        'closed_date': self._get_current_datetime()})
            self.write(self._get_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate9(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'cancelled'
            self.write({'cancel_user_id': self.env.user.id,
                        'cancel_date': self._get_current_datetime()})
            self.write(
                self._get_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate10(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'draft'
            av = service.overtime_claim_policy_id.hr_attendance_verification\
                if service.overtime_claim_policy_id else False
            self.write({
                'submit_date': False,
                'submitted_by': False,
                'mngr_user_id': False,
                'mngr_approval_date': False,
                'vp_user_id': False,
                'vp_approval_date': False,
                'hr_user_id': False,
                'hr_approval_date': False,
                'budget_user_id': False,
                'budget_approval_date': False,
                'ceo_user_id': False,
                'ceo_approval_date': False,
                'approved_user_id': False,
                'approved_date': False,
                'closed_user_id': False,
                'closed_date': False,
                'locked_user_id': False,
                'locked_date': False,
                'rejected_user_id': False,
                'rejected_date': False,
                'cancel_user_id': False,
                'cancel_date': False,
                'expected_approval_date_as_sla': False,
                'final_approval_date': False,
                'final_approval_user_id': False,
                'waiting_time': False,
                'verify_attendance': av,

            })
            self.write({'reset_user_id': self.env.user.id,
                        'reset_date': self._get_current_datetime()})
            self.write(
                self._get_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate11(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'approved'
            final_approval = {
                'final_approval_user_id': self.env.user.id,
                'final_approval_date': self._get_current_datetime(),
                'approved_user_id': self.env.user.id, 'approved_date':
                    self._get_current_datetime()
            }
            self.write(final_approval)
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate12(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'payroll_processing'
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate13(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'closed'
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_submit_mngr(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = self._get_dest_state(service)
            if dest_state:
                self.write(
                    self._get_approval_info(service,
                                            dest_state))
                self.check_dest_state_send_email(dest_state)
        return True

    # All Button Comman method
    @api.multi
    def _check_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.overtime_claim_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You cannot submit the request without attaching a '
                          'document.\n For attaching a document: press save'
                          ' then attach a document.'))
            if not service.employee_id.parent_id:
                raise Warning(_(
                    'Please, Ask your HR team to complete your profile data.'))
            if service.overtime_claim_policy_id.endorsement_required and not \
                    service.endorsement_approved:
                raise Warning(
                    _("Please, You should agree on the endorsement "
                      "to proceed with your request."))
            quantity_required = \
                service.overtime_claim_policy_id.quantity_required
            request_max_quantity = \
                service.overtime_claim_policy_id.request_max_quantity
            if quantity_required and service.quantity > request_max_quantity:
                raise Warning(
                    _("Please, You aren't allowed to request more "
                      "than %s %s/s per request.") %
                    (request_max_quantity,
                     service.overtime_claim_policy_id.name))
                # job_position_required = \
                #     service.overtime_claim_policy_id.job_position_required
                # users_obj = self.env['res.users']
                # if job_position_required and not users_obj.has_group(
                #         'service_management.group_service_hiring_srvs'):
                #     raise Warning(
                #         _("Please, Make sure that
                #  you have the rights to apply for"
                #           "the hiring request."))
        return True

    @api.multi
    def _check_group(self, group_xml_id):
        users_obj = self.env['res.users']
        if users_obj.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def _check_user_permissions(self, signal='approve'):
        for rec in self:
            if not rec._check_group(
                    'hr_overtime.group_overtime_self_approval_srvs',
            ):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(
                        _(
                            "Please, Make sure that you have the rights to %s "
                            "your own request.") %
                        (signal))
        return False

    # def _get_draft_state(self):
    #     draft_state = self.env['service.panel.displayed.states'].search([
    #         ('wkf_state', '=', 'draft'),
    #         ], limit=1)
    #     return draft_state

    @api.multi
    def _get_dest_state(self, service):
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

    @api.multi
    def _get_dest_email_to(self, rec):
        email_to = None
        current_state = rec.state
        if current_state == 'mngr_approval':
            email_to = rec.employee_id.overtime_manager_id.work_email
        elif current_state == 'vp_approval':
            email_to = rec.employee_id.overtime_vp_id.work_email
        elif current_state == 'hr_approval':
            email_to = rec.overtime_claim_policy_id.hr_email
        elif current_state == 'budget_approval':
            email_to = rec.pre_approval_policy_id.budget_email
        elif current_state == 'ceo_approval':
            email_to = rec.employee_id.overtime_ceo_id.work_email
        return email_to

    @api.multi
    def _get_approval_delay(self, rec, req_approvals):
        diff = last_approval_date = current_state_index = False
        current_state_index = req_approvals.index(rec.state)
        if current_state_index == 0:
            last_approval_date = rec.submit_date
        else:
            previous_state = req_approvals[current_state_index - 1]
            if previous_state == 'mngr_approval':
                last_approval_date = rec.mngr_approval_date
            elif previous_state == 'vp_approval':
                last_approval_date = rec.vp_approval_date
            elif previous_state == 'hr_approval':
                last_approval_date = rec.hr_approval_date
            elif previous_state == 'budget_approval':
                last_approval_date = rec.budget_approval_date
            elif previous_state == 'ceo_approval':
                last_approval_date = rec.ceo_approval_date
        if last_approval_date:
            last_approval_date = datetime.strptime(last_approval_date,
                                                   DTF).date()
            now = datetime.strptime(self._get_current_datetime(), DTF).date()
            diff = relativedelta(now, last_approval_date)
        return diff

    @api.multi
    def send_reminder(self):
        # context = dict(context or {})
        delay_to_remind = 1
        # If there is no any linked reminder criteria,
        # the system will send a daily reminder.
        where_clause = [
            ('state', 'not in', ['draft', 'rejected', 'closed', 'locked',
                                 'approved', 'cancelled']),
            ('submit_date', '<', datetime.now().strftime('%Y-%m-%d 00:00:00'))
        ]
        excluded_ids = self.search(where_clause)
        for rec in excluded_ids:
            req_approvals = rec._get_service_req_approvals()
            if rec.state in req_approvals:
                # It may happen in case of changing the required approvals
                # before finalizing the pending, so it will be skipped.
                approval_delay_diff = rec._get_approval_delay(rec,
                                                              req_approvals)
                if rec.overtime_claim_policy_id.approval_reminder_line:
                    delay_to_remind = rec.overtime_claim_policy_id. \
                        approval_reminder_line.delay
                if approval_delay_diff.days > delay_to_remind:
                    email_to = self._get_dest_email_to(rec)
                    et_id = 'hr_overtime.' \
                            'overtime_approval_reminder_cron_email_template'
                    rec._send_email(et_id, email_to, rec.state, rec.id,
                                    'overtime_statement_request')
        return True

    @api.model
    def send_pre_approval_submit_reminder(self):
        email_to = self.employe_id.work_email
        if self.state == 'draft':
            self.send_email(
                'hr_overtime.overtime_submit_reminder_cron_email_template',
                email_to,
                'draft',
                'overtime_pre_request',
            )


class OvertimeClaimActivity(models.Model):
    _name = 'overtime.claim.activity'
    _order = 'date asc'

    date = fields.Date('Date', default=date.today())
    activity_planned = fields.Text('Activity')
    # day_cost = fields.Float(string='Day Cost')
    remark = fields.Text('Remarks')
    overtime_claim_id = fields.Many2one('overtime.statement.request',
                                        'Overtime '
                                        'Claim')
    expected_hours = fields.Float(string='Expected Hours')
    remaining_hours = fields.Float(string='Remaining Hours')
    actual_hours = fields.Float('Actual Hours')
    calculated_hours = fields.Float('Calculated Hours')
    actual_day_cost = fields.Monetary(string='Actual Day Cost')
    attendance_hours = fields.Float(string='Attendance')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    state = fields.Selection(SERVICE_STATUS,
                             related='overtime_claim_id.state',
                             string='Status',
                             store=True)
    employee_id = fields.Many2one('hr.employee',
                                  related='overtime_claim_id.employee_id',
                                  string='Employee', store=True)

    @api.model
    def check_in_pre_request(self):
        # date_lst = []
        pre_approval_obj = self.env['overtime.pre.request']
        context = dict(self._context)
        if context.get('pre_approval_request_id'):
            pre_approval_request_rec = pre_approval_obj.browse(context.get(
                'pre_approval_request_id'))
            if pre_approval_request_rec:
                for line in pre_approval_request_rec.plan_activity_ids:
                    date = self.date or context.get('r_date')
                    if line.date == date:
                        return line.expected_hours - line.approved_hours
                        # date_lst.append(line.date)
                        # if self.date not in date_lst:
                        #     raise Warning(_('Please make sure you have
                        # approval for %s '
                        #                     'date If
                        #  you not have approval kindly '
                        #                     'contact to HR
                        # team or make overtime '
                        #                     'pre-request'))
            return 0.0

    @api.model
    def create(self, vals):
        context = dict(self._context)
        if not context.get('from_button') and vals.get(
                'overtime_claim_id'):
            if vals.get('overtime_claim_id'):
                overtime_claim_rec = self.env[
                    'overtime.statement.request'].browse(
                    vals.get('overtime_claim_id'))
                if overtime_claim_rec.pre_approval_request_id:
                    pre_approval_request_rec = \
                        overtime_claim_rec.pre_approval_request_id.id
                    context.update(
                        {'pre_approval_request_id': pre_approval_request_rec,
                         'r_date': vals.get('date')})
                    expected_hours = self.with_context(
                        context).check_in_pre_request() or 0.0
                    actual_hours = vals.get('actual_hours') if vals.get(
                        'actual_hours') else self.actual_hours
                    remaining_hours = (expected_hours - actual_hours) or 0.0
                    vals.update({'expected_hours': expected_hours,
                                 'remaining_hours': remaining_hours})
        return super(OvertimeClaimActivity, self).create(vals)

    @api.multi
    def write(self, vals):
        context = dict(self._context)
        for rec in self:
            if not context.get('from_button'):
                if (vals.get(
                        'overtime_claim_id') and vals.get(
                    'overtime_claim_id').pre_approval_request_id) or \
                        (rec.overtime_claim_id and
                            rec.overtime_claim_id.pre_approval_request_id):
                    pre_approval_request_rec = vals.get(
                        'overtime_claim_id').pre_approval_request_id.id if \
                        vals.get('overtime_claim_id') else \
                        rec.overtime_claim_id.pre_approval_request_id.id
                    context.update(
                        {'pre_approval_request_id': pre_approval_request_rec,
                         'r_date': vals.get('date' or self.date)})
                    expected_hours = self.with_context(
                        context).check_in_pre_request() or 0.0
                    actual_hours = vals.get('actual_hours') if vals.get(
                        'actual_hours') else self.actual_hours
                    remaining_hours = (expected_hours - actual_hours) or 0.0
                    vals.update({'expected_hours': expected_hours,
                                 'remaining_hours': remaining_hours})
        return super(OvertimeClaimActivity, self).write(vals)

    def _check_overtime_lines_maximum_hours(self, claim_request_policy_id,
                                            date, employee_id):
        overtime_statement_obj = self.env['overtime.statement.request']
        first_date, last_date = \
            overtime_statement_obj._get_month_first_last_date(date)
        year_first_date, year_last_date = \
            overtime_statement_obj._get_year_first_last_date(date)
        overtime_statement_obj. \
            _check_day_maximum_hours(date, date, claim_request_policy_id,
                                     employee_id, self.actual_hours)
        overtime_statement_obj. \
            _check_month_maximum_hours(first_date, last_date,
                                       claim_request_policy_id, employee_id,
                                       self.actual_hours)
        overtime_statement_obj. \
            _check_year_maximum_hours(year_first_date, year_last_date,
                                      claim_request_policy_id, employee_id,
                                      self.actual_hours)

    @api.onchange('actual_hours', 'date')
    def calculate_day_cost(self):
        context = dict(self._context)
        actual_day_cost, expected_hours, total_remaning_hours, \
        calculated_hours = 0.0, 0.0, 0.0, 0.0
        overtime_calculation_line_obj = self.env[
            'overtime.calculation.line']
        if not self.overtime_claim_id.overtime_claim_policy_id:
            pass
        if context.get('employee_id'):
            employee_id = context.get('employee_id')
            employee_rec = self.env['hr.employee'].browse(employee_id)
            claim_request_policy_id = \
                self.overtime_claim_id.overtime_claim_policy_id
            # self._check_overtime_lines_maximum_hours(
            #     claim_request_policy_id, date, employee_id)
            if context.get('pre_approval_request_id'):
                expected_hours = self.with_context(
                    context).check_in_pre_request()
                total_remaning_hours = (expected_hours - self.actual_hours)
            if self.date and claim_request_policy_id and self.actual_hours:
                actual_day_cost = \
                    overtime_calculation_line_obj.calculate_date_day_cost(
                        self.date, self.actual_hours,
                        claim_request_policy_id,
                        employee_rec)
                calculated_hours = \
                    overtime_calculation_line_obj.calculate_date_day(
                        self.date, self.actual_hours,
                        claim_request_policy_id, employee_rec)
        self.calculated_hours = calculated_hours
        self.actual_day_cost = actual_day_cost
        self.expected_hours = expected_hours
        self.remaining_hours = total_remaning_hours
