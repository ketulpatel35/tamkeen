from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import ValidationError

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
                  ('approved', 'Approved'),
                  ('rejected', 'Rejected'),
                  ('open', 'Claim'),
                  ('closed', 'Closed'),
                  ('locked', 'Locked'),
                  ('cancelled', 'Cancelled'), ('payroll_processing',
                                               'Payroll Processing')]


class HrOvertimePreRequest(models.Model):
    _name = 'overtime.pre.request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Overtime Pre-Approval Request'

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def clear_lines(self):
        for rec in self:
            for line in rec.plan_activity_ids:
                line.unlink()
        return True

    @api.depends('plan_activity_ids.expected_hours')
    def compute_total_planed_hours(self):
        """
        compute total planed hours.
        :return:
        """
        expected_hours = 0
        for rec in self:
            for line in rec.plan_activity_ids:
                expected_hours += line.expected_hours
            rec.total_number_of_hrs_requested = expected_hours

    @api.depends('plan_activity_ids.approved_hours')
    def _compute_total_approved_hours(self):
        """
        compute total planed hours.
        :return:
        """
        approved_hours = 0
        for rec in self:
            for line in rec.plan_activity_ids:
                approved_hours += line.approved_hours
            rec.total_taken_hours = approved_hours

    @api.multi
    def compute_remaining_hours_balance(self):
        for rec in self:
            rec.remaining_hours_balance = rec.total_number_of_hrs_requested \
                - rec.total_taken_hours

    @api.depends('plan_activity_ids.day_cost')
    def compute_pre_requested_total_cost(self):
        """
        compute total planed hours.
        :return:
        """
        total_cost = 0
        for rec in self:
            for line in rec.plan_activity_ids:
                total_cost += line.day_cost
            rec.pre_requested_total_cost = total_cost

    @api.depends('plan_activity_ids.day_cost')
    def compute_pre_requested_total_cost(self):
        """
        compute total planed hours.
        :return:
        """
        total_cost = 0
        for rec in self:
            for line in rec.plan_activity_ids:
                total_cost += line.day_cost
            rec.pre_requested_total_cost = total_cost

    @api.depends('plan_activity_ids.approved_hours')
    def compute_total_taken_cost(self):
        """
        compute total planed hours.
        :return:
        """
        total_taken_cost = 0
        overtime_calculation_line_obj = self.env['overtime.calculation.line']
        for rec in self:
            for line in rec.plan_activity_ids:
                day_cost = \
                    overtime_calculation_line_obj.calculate_date_day_cost(
                        line.date, line.approved_hours,
                        rec.pre_approval_policy_id,
                        rec.employee_id)
                total_taken_cost += day_cost
            rec.taken_total_cost = total_taken_cost

    @api.depends('final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.submit_date:
                submit_date = datetime.strptime(rec.submit_date, OE_DTFORMAT)
                if rec.final_approval_date:
                    final_approval_date = datetime.strptime(
                        rec.final_approval_date, OE_DTFORMAT)
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
            sla_period = rec.pre_approval_policy_id.sla_period or False
            sla_period_unit = rec.pre_approval_policy_id.sla_period_unit or \
                False
            if sla_period and sla_period_unit:
                if rec.submit_date:
                    submit_date = datetime.strptime(rec.submit_date,
                                                    OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    name = fields.Char('Reference', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self:
                                  self.env['hr.employee'].search([
                                      ('user_id', '=', self._uid)],
                                      limit=1) or False,
                                  track_visibility='onchange')
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee Company ID')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Organization Unit', store=True)
    request_date = fields.Date('Request Date',
                               default=lambda d: datetime.today().date(),
                               track_visibility='onchange')
    cost_center_id = fields.Many2one('bs.costcentre',
                                     string='Cost Center',
                                     track_visibility='onchange',
                                     help='Select the cost center which will'
                                          ' be affected by this request cost.',
                                     copy=False)
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          track_visibility='onchange',
                                          string="Analytic Account")
    plan_activity_ids = fields.One2many('overtime.planned.activity',
                                        'pre_request_id',
                                        string='Planned Activities',
                                        copy=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    total_number_of_hrs_requested = fields.Float(
        'Total Pre-Requested Hours', compute='compute_total_planed_hours',
        store=True
    )
    pre_requested_total_cost = fields.Monetary(
        string='Total Cost (Pre-Requested)',
        compute='compute_pre_requested_total_cost')
    total_taken_hours = fields.Float(compute='_compute_total_approved_hours',
                                     string='Total Taken Hours')
    taken_total_cost = fields.Monetary(compute='compute_total_taken_cost',
                                       string='Total Cost (Taken)')
    remaining_hours_balance = fields.Float(
        string='Remaining Hours Balance',
        compute='compute_remaining_hours_balance')
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
                                       copy=False, track_visibility='onchange')
    cancel_user_id = fields.Many2one('res.users', string='Cancel By',
                                     readonly=True, copy=False,
                                     )
    cancel_date = fields.Datetime(string='Cancel Date',
                                  readonly=True, copy=False,
                                  )

    open_user_id = fields.Many2one('res.users', string='Open By',
                                   readonly=True, copy=False,
                                   )
    open_date = fields.Datetime(string='Open Date',
                                readonly=True, copy=False,
                                )

    locked_user_id = fields.Many2one('res.users', string='Locked By',
                                     readonly=True, copy=False,
                                     )
    locked_date = fields.Datetime(string='Locked Date',
                                  )
    closed_user_id = fields.Many2one('res.users', string='Closed By',
                                     readonly=True, copy=False,
                                     )
    closed_date = fields.Datetime(string='Closed Date',
                                  track_visibility='onchange')
    return_user_id = fields.Many2one('res.users', string='Return By',
                                     readonly=True, copy=False,
                                     )
    return_date = fields.Datetime(string='Return Date',
                                  readonly=True, copy=False, )

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
                                 string='Company', track_visibility='onchange')
    pre_approval_policy_id = fields.Many2one('service.configuration.panel',
                                             string='Policy')
    about_service = fields.Text(
        string='About The Service',
        related='pre_approval_policy_id.about_service',
        readonly=True,
        store=True)
    submit_message = fields.Text(
        related='pre_approval_policy_id.submit_message',
        string='Submit Hint Message', store=True)
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
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]})
    waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                               string='Waiting Time',
                               method=True, copy=False,
                               states={'draft': [('readonly', False)]})
    endorsement_required = fields.Boolean(string='Endorsement Required',
                                          invisible=True)
    endorsement_text = fields.Text(
        related='pre_approval_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True)
    endorsement_approved = fields.Boolean(string='Endorsement Approved',
                                          track_visibility='onchange',
                                          readonly=1,
                                          states={
                                              'draft': [
                                                  ('readonly',
                                                   False)]},
                                          )
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', pre_approval_policy_id)]",
        copy=False)
    service_log_ids = fields.One2many('service.log',
                                      'overtime_pre_request_id',
                                      string='Service Logs')
    file_to_fill = fields.Binary(
        related='pre_approval_policy_id.file_to_fill',
        string='File To Fill',
        help="The required template that should be filled by the requester.",
        readonly=True,
        copy=False,
        states={
            'draft': [
                ('readonly',
                 False)]},
        store=True)

    @api.multi
    def service_validate10(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'draft'
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
                'open_user_id': False,
                'open_date': False,
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
            })
            self.write({'return_user_id': self.env.user.id, 'return_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
        return True

    def _get_pre_request_policy_id(self):
        if self.company_id and self.company_id.overtime_policy_id:
            if self.company_id.overtime_policy_id.valid_from_date and \
                    self.company_id.overtime_policy_id.valid_to_date and \
                    self.company_id.overtime_policy_id.pre_request_id:
                today_date = datetime.today().date()
                from_date = datetime.strptime(
                    self.company_id.overtime_policy_id.pre_request_id
                        .valid_from_date, DF).date()
                to_date = datetime.strptime(
                    self.company_id.overtime_policy_id.
                        pre_request_id.valid_to_date, DF).date()
                if from_date <= today_date <= to_date:
                    return self.company_id.overtime_policy_id.pre_request_id
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
        pre_request_id = self._get_pre_request_policy_id()
        if not pre_request_id:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the policy is applied.'))
        self.pre_approval_policy_id = pre_request_id.id

    @api.onchange('pre_approval_policy_id')
    def onchange_pre_approval_policy_id(self):
        if self.pre_approval_policy_id and \
                self.pre_approval_policy_id.states_to_display_ids:
            self.stage_id = \
                self.pre_approval_policy_id.states_to_display_ids[0].id
        if self.pre_approval_policy_id:
            self.endorsement_required = \
                self.pre_approval_policy_id.endorsement_required

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        if vals:
            seq = self.env['ir.sequence'].next_by_code('pre.overtime')
            vals.update({'name': seq})
        res = super(HrOvertimePreRequest, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        """
        :return:
        """
        res = []
        for rec in self:
            employee_name = rec.employee_id.name
            name = rec.name
            if employee_name and name:
                name = employee_name + '[' + rec.name + ']' + '-' + \
                    '(Balance:' + str(rec.remaining_hours_balance) + ')'
            res.append((rec.id, name))
        return res

    @api.multi
    def unlink(self):
        for overtime in self:
            if overtime.state != 'draft':
                raise ValidationError(_('You can only delete '
                                        'the draft requests!'))
        return super(HrOvertimePreRequest, self).unlink()

    @api.multi
    def _get_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'overtime.pre.request')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'hr_overtime.open_overtime_pre_request_for_view_all'
        if dest_state == 'hr_approval':
            window_action_ref = \
                'hr_overtime.open_overtime_pre_request_for_hr'
        if dest_state in ['mngr_approval', 'vp_approval', 'ceo_approval']:
            window_action_ref = \
                'hr_overtime.open_overtime_mngr_pre_request_approval'
        if dest_state == 'budget_approval':
            window_action_ref = \
                'hr_overtime.open_overtime_pre_request_for_budget'
        if dest_state in ['cancelled', 'locked', 'open', 'rejected', 'closed']:
            window_action_ref = \
                'hr_overtime.open_overtime_pre_ess_requests'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

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
            result.update({'state': dest_state, 'vp_user_id': self.env.user.id,
                           'vp_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state, 'budget_user_id': self.env.user.id,
                 'budget_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'hr_user_id': self.env.user.id,
                 'hr_approval_date': self._get_current_datetime()})
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
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.pre_approval_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.pre_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.pre_approval_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.pre_approval_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.pre_approval_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
        return req_approvals

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
                'hr_overtime.overtime_pre_req_send_to_vp',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'hr_overtime.overtime_pre_req_send_manager',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'budget_approval':
            self._send_email(
                'hr_overtime.overtime_pre_req_send_to_budget',
                None, dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'hr_approval':
            self._send_email(
                'hr_overtime.overtime_pre_req_send_to_hr', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'ceo_approval':
            self._send_email(
                'hr_overtime.overtime_pre_req_send_to_ceo', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'open':
            self._send_email(
                'hr_overtime.overtime_pre_req_approved', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'rejected':
            self.with_context(context)._send_email(
                'hr_overtime.email_template_pre_overtime_reject', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'locked':
            self._send_email(
                'hr_overtime.email_template_pre_overtime_locked', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'closed':
            self._send_email(
                'hr_overtime.email_template_pre_overtime_closed', None,
                dest_state, self.id, 'overtime_pre_request')
        elif dest_state == 'cancelled':
            self._send_email(
                'hr_overtime.email_template_pre_overtime_cancelled', None,
                dest_state, self.id, 'overtime_pre_request')
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
            dest_state = 'open'
            final_approval = {
                'final_approval_user_id': self.env.user.id,
                'final_approval_date': self._get_current_datetime(),
                'open_user_id': self.env.user.id, 'open_date':
                    self._get_current_datetime()
            }
            self.write(final_approval)
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
            self.write({'rejected_user_id': self.env.user.id, 'rejected_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.with_context(context).check_dest_state_send_email(
                dest_state)
        return True

    @api.multi
    def service_validate7(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'locked'
            self.write({'locked_user_id': self.env.user.id, 'locked_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate8(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'closed'
            self.write({'closed_user_id': self.env.user.id, 'closed_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate9(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'cancelled'
            self.write({'cancel_user_id': self.env.user.id, 'cancel_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate11(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_service_restrictions()
            dest_state = 'open'
            self.write({'open_user_id': self.env.user.id, 'open_date':
                        self._get_current_datetime()})
            self.write(
                self._get_approval_info(service,
                                        dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    # All Button Comman method
    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have to check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.service_validate4()
        else:
            return False
        return True

    @api.multi
    def _check_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.pre_approval_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachement = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachement:
                    raise Warning(
                        _('You cannot submit the request without attaching a '
                          'document.\n For attaching a document: press save '
                          'then attach a document.'))
            if not service.employee_id.parent_id:
                raise Warning(_(
                    'Please, Ask your HR team to complete your profile data.'))
            if service.pre_approval_policy_id.endorsement_required and not \
                    service.endorsement_approved:
                raise Warning(
                    _("Please, You should agree on the endorsement to proceed "
                      "with your request."))
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
                        _("Please, Make sure that you have the rights to %s "
                          "your own request.") %
                        (signal))
        return False

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
        service_states.append('open')  # to add the approved state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

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
                # self._send_email('hr_overtime.overtime_pre_req_send_manager')
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

    def _get_maximum_monthly_hours(self, pre_approval_policy_id):
        if pre_approval_policy_id:
            maximum_hours_per_month = \
                pre_approval_policy_id.maximum_hours_per_month
            return maximum_hours_per_month

    def _get_maximum_yearly_hours(self, pre_approval_policy_id):
        if pre_approval_policy_id:
            maximum_hours_per_year = \
                pre_approval_policy_id.maximum_hours_per_year
            return maximum_hours_per_year

    def _get_maximum_day_hours(self, pre_approval_policy_id):
        overtime_type_check = []
        for line in pre_approval_policy_id.overtime_calculation_line_ids:
            if line.type == 'daily':
                maximum_hours_per_day = line.maximum_hour
                type = line.type
                overtime_type_check.append(str(line.type))
                return maximum_hours_per_day, type
        if str('daily') not in overtime_type_check:
            raise Warning(_('No maximum daily configuration is set. '
                            'Please contact HR to proceed your request.'))

    def _get_maximum_rest_days(self, pre_approval_policy_id):
        overtime_type_check = []
        for line in pre_approval_policy_id.overtime_calculation_line_ids:
            if line.type == 'rest_day':
                type = line.type
                maximum_hours_per_rest_day = line.maximum_hour
                overtime_type_check.append(str(line.type))
                return maximum_hours_per_rest_day, type
        if str('rest_day') not in overtime_type_check:
            raise Warning(_('No maximum rest days configuration is set.'
                            'Please contact HR to proceed your request.'))

    def _get_maximum_public_holidays(self, pre_approval_policy_id):
        overtime_type_check = []
        for line in pre_approval_policy_id.overtime_calculation_line_ids:
            if line.type == 'public_holiday':
                type = line.type
                maximum_hours_per_public_holiday = line.maximum_hour
                overtime_type_check.append(str(line.type))
                return maximum_hours_per_public_holiday, type
        if str('public_holiday') not in overtime_type_check:
            raise Warning(_('No maximum public holidays configuration is '
                            'set.'
                            'Please contact HR to proceed your request.'))

    def _get_planned_activity(self, first_date, last_date, employee_id):
        overtime_planned_activity_rec = self.env[
            'overtime.planned.activity']. \
            search([('date', '>=', first_date),
                    ('date', '<=', last_date), ('pre_request_id.employee_id',
                                                '=', employee_id.id)])
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
                                 pre_approval_policy_id, employee_id):
        expected_total_hours = 0.0
        hours_more_than_date = ''

        public_holiday_obj = self.env['hr.holidays.public']
        if len(pre_approval_policy_id.overtime_calculation_line_ids) >= 1:
            if first_date.weekday() in self._get_rest_days(employee_id):
                maximum_hours, type = self._get_maximum_rest_days(
                    pre_approval_policy_id)
            elif public_holiday_obj.is_public_holiday(first_date):
                maximum_hours, type = self._get_maximum_public_holidays(
                    pre_approval_policy_id)
            else:
                maximum_hours, type = self._get_maximum_day_hours(
                    pre_approval_policy_id)
            overtime_planned_activity_rec = self._get_planned_activity(
                first_date, last_date, employee_id)
            for planned_activity in overtime_planned_activity_rec:
                expected_total_hours += planned_activity.expected_hours
            if expected_total_hours > maximum_hours:
                hours_more_than_date = str(first_date).split(' ')[0] if len(
                    str(first_date).split(' ')) > 1 else ''
        else:
            raise Warning(_('There are no configuration for overtime in '
                            'policy. For more information contact to HR.'))
        return maximum_hours, type, hours_more_than_date

    def _check_month_maximum_hours(self, first_date, last_date,
                                   pre_approval_policy_id, employee_id):
        expected_total_hours = 0.0
        hours_more_than_month_first_date, hours_more_than_month_last_date = \
            '', ''
        maximum_hours_per_month = self._get_maximum_monthly_hours(
            pre_approval_policy_id)
        overtime_planned_activity_rec = self._get_planned_activity(first_date,
                                                                   last_date,
                                                                   employee_id)
        for planned_activity in overtime_planned_activity_rec:
            expected_total_hours += planned_activity.expected_hours
        if expected_total_hours > \
                maximum_hours_per_month:
            hours_more_than_month_first_date = str(first_date).split(' ')[0]\
                if len(str(first_date).split(' ')) > 1 else ''
            hours_more_than_month_last_date = str(last_date).split(' ')[0] \
                if len(str(last_date).split(' ')) > 1 else ''
        return hours_more_than_month_first_date, \
            hours_more_than_month_last_date, maximum_hours_per_month

    def _check_year_maximum_hours(self, first_date, last_date,
                                  pre_approval_policy_id, employee_id):
        expected_total_hours = 0.0
        maximum_hours_per_year = self._get_maximum_yearly_hours(
            pre_approval_policy_id)
        overtime_planned_activity_rec = self._get_planned_activity(first_date,
                                                                   last_date,
                                                                   employee_id)
        for planned_activity in overtime_planned_activity_rec:
            expected_total_hours += planned_activity.expected_hours
        if expected_total_hours > \
                maximum_hours_per_year:
            raise Warning(_('You are not allowed to request more than %s '
                            'hour/s per year.') % maximum_hours_per_year)

    def _check_planned_activity(self, plan_activity_ids):
        if not plan_activity_ids:
            raise Warning(_('You should have at least one planned activity.'))
        return True

    def check_maximum_hours(self, pre_approval_policy_id, plan_activity_ids):
        line_date_day = line_date_weekend = line_date_rest_day = \
            line_date_public_holiday = ''
        total_hours_day = total_hours_weekend = total_hours_rest = \
            total_public_holiday = 0.0
        hours_more_than_month_first_date = ''
        hours_more_than_month_last_date = ''
        maximum_hours_per_month = ''
        warning = ''

        for line in plan_activity_ids:
            if line.date:
                date = datetime.strptime(line.date, DF)
                first_date, last_date = self._get_month_first_last_date(date)
                year_first_date, year_last_date = \
                    self._get_year_first_last_date(date)
                employee_id = self.employee_id

                total_hours, day_type, date_day = \
                    self._check_day_maximum_hours(date, date,
                                                  pre_approval_policy_id,
                                                  employee_id)
                if date_day and day_type == 'daily':
                    line_date_day += str(line.date) + ', '
                    total_hours_day = total_hours
                elif date_day and day_type == 'weekday':
                    line_date_weekend += str(line.date) + ', '
                    total_hours_weekend = total_hours
                elif date_day and day_type == 'rest_day':
                    line_date_rest_day += str(line.date) + ', '
                    total_hours_rest = total_hours
                elif date_day and day_type == 'public_holiday':
                    line_date_public_holiday += str(line.date) + ', '
                    total_public_holiday = total_hours
                hours_more_than_month_first_date, \
                    hours_more_than_month_last_date, maximum_hours_per_month\
                    = self._check_month_maximum_hours(first_date, last_date,
                                                      pre_approval_policy_id,
                                                      employee_id)
                self._check_year_maximum_hours(year_first_date, year_last_date,
                                               pre_approval_policy_id,
                                               employee_id)
        if hours_more_than_month_first_date and \
                hours_more_than_month_last_date:
            warning += 'You are not allowed to request more than %s ' \
                       'hour/s for Month . For more information you ' \
                       'can check between from %s to %s Dates.' % (
                           str(maximum_hours_per_month),
                           hours_more_than_month_first_date,
                           hours_more_than_month_last_date)
        if line_date_day:
            warning += '\nYou are not allowed to request more than %s ' \
                       'hour/s for Normal Days . For more information you ' \
                       'can check for %s.' % (str(total_hours_day),
                                              line_date_day)
        if line_date_weekend:
            warning += '\nYou are not allowed to request more than %s ' \
                       'hour/s for Weekend . For more information you ' \
                       'can check for %s.' % (str(total_hours_weekend),
                                              line_date_weekend)
        if line_date_rest_day:
            warning += '\nYou are not allowed to request more than %s ' \
                       'hour/s for Weekend . For more information you ' \
                       'can check for %s.' % (str(total_hours_rest),
                                              line_date_rest_day)
        if line_date_public_holiday:
            warning += '\nYou are not allowed to request more than %s ' \
                       'hour/s for Public Holiday . For more information you' \
                       ' can check for %s.' % (str(total_public_holiday),
                                               line_date_public_holiday)
        if warning:
            raise Warning(_(warning))
        return True

    @api.multi
    def check_repeated_date(self):
        date_list = []
        date_check_list = []
        for rec in self:
            for line in rec.plan_activity_ids:
                date_list.append(str(line.date))
            for date_lst in date_list:
                if date_lst not in date_check_list:
                    date_check_list.append(date_lst)
                else:
                    raise Warning(_("Kindly, Don't use the same date more "
                                    "than one time."))

    def _check_expected_hours(self):
        for line in self.plan_activity_ids:
            if line.expected_hours <= 0:
                raise Warning(
                    _('Expected hours should be greater than 0.'))
        return True

    # New [Submit for Approval]
    @api.multi
    def action_submit_for_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        for rec in self:
            rec._check_expected_hours()
            if rec.employee_id and rec.employee_id.user_id:
                if rec.employee_id.user_id.id != self.env.user.id:
                    raise Warning(_('Only  %s can submit this request !') %
                                  rec.employee_id.name)
            if not rec.pre_approval_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the policy is applied.'))
            rec.check_repeated_date()
            rec._check_planned_activity(rec.plan_activity_ids)
            rec.check_maximum_hours(rec.pre_approval_policy_id,
                                    rec.plan_activity_ids)
        self._check_point_for_all_stage()

    @api.multi
    def open_statement(self):
        obj_statement = self.env['overtime.statement.request']
        statements_ids = obj_statement.search([
            ('pre_approval_request_id', 'in', self.ids)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overtime Claim Request'),
            'res_model': 'overtime.statement.request',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', statements_ids.ids)],
            'res_id': statements_ids.ids,
            'target': 'current',
        }

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
            'model': 'overtime.pre.request'
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
    def _get_dest_email_to(self, rec):
        email_to = None
        current_state = rec.state
        if current_state == 'mngr_approval':
            email_to = rec.employee_id.overtime_manager_id.work_email
        elif current_state == 'vp_approval':
            email_to = rec.employee_id.overtime_vp_id.work_email
        elif current_state == 'hr_approval':
            email_to = rec.pre_approval_policy_id.hr_email
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
                                                   OE_DTFORMAT)
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            diff = relativedelta(now, last_approval_date)
        return diff

    @api.model
    def send_reminder(self):
        # context = dict(context or {})
        delay_to_remind = 1
        # If there is no any linked reminder criteria,
        # the system will send a daily reminder.
        where_clause = [
            ('state', 'not in', ['draft', 'rejected', 'closed', 'locked',
                                 'open', 'cancelled']),
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
                if rec.pre_approval_policy_id.approval_reminder_line:
                    delay_to_remind = \
                        rec.pre_approval_policy_id.approval_reminder_line.delay
                if approval_delay_diff.days > delay_to_remind:
                    email_to = self._get_dest_email_to(rec)
                    rec._send_email(
                        'hr_overtime.pre_overtime_'
                        'approval_reminder_cron_email_template',
                        email_to, rec.state, rec.id, 'overtime_pre_request')
        return True

    @api.model
    def send_pre_approval_submit_reminder(self):
        email_to = self.employee_id.work_email
        if self.state == 'draft':
            self.send_email(
                'hr_overtime.'
                'pre_overtime_approval_reminder_cron_email_template',
                email_to, 'draft', 'overtime_pre_request',
            )


class OvertimePlannedActivity(models.Model):
    _name = 'overtime.planned.activity'
    _order = 'date asc'

    date = fields.Date('Date', default=date.today())
    activity_planned = fields.Text('Activity')
    expected_hours = fields.Float('Expected Hours')
    approved_hours = fields.Float(string='Claimed Hours')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)
    day_cost = fields.Monetary(string='Day Cost')
    actual_day_cost = fields.Float(string='Actual Day Cost')
    remark = fields.Text('Remarks')
    pre_request_id = fields.Many2one('overtime.pre.request', 'Pre Request')
    actual_hours = fields.Float('Actual Hours')
    state = fields.Selection(SERVICE_STATUS, related='pre_request_id.state',
                             string='Status',
                             store=True)

    @api.model
    def calculate_day_cost(self):
        overtime_calculation_line_obj = self.env['overtime.calculation.line']
        day_cost = 0.0
        context = dict(self._context)
        if context.get('employee_id'):
            employee_id = context.get('employee_id')
            employee_rec = self.env['hr.employee'].browse(employee_id)
            if not self.pre_request_id.pre_approval_policy_id and not \
                    context.get('pre_approval_policy_id'):
                pass
            pre_request_policy_id = context.get(
                'pre_request_policy_id') if context.get(
                'pre_request_policy_id') else \
                self.pre_request_id.pre_approval_policy_id
            date = context.get('r_date') if context.get('r_date') else \
                self.date
            expected_hours = context.get('expected_hours') if context.get(
                'expected_hours') else \
                self.expected_hours
            if date and expected_hours and pre_request_policy_id:
                day_cost = \
                    overtime_calculation_line_obj.calculate_date_day_cost(
                        date, expected_hours, pre_request_policy_id,
                        employee_rec)
        return day_cost

    @api.onchange('expected_hours', 'date')
    def onchange_calculate_day_cost(self):
        context = dict(self._context)
        day_cost = self.with_context(context).calculate_day_cost()
        self.day_cost = day_cost
