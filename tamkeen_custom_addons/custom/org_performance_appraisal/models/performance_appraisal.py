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


class PerformanceAppraisal(models.Model):
    _name = 'performance.appraisal'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Appraisal Performance'
    _order = 'name desc'

    SERVICE_STATUS = [('draft', 'To Submit'),
                      ('mngr_approval', 'Direct Manager'),
                      ('vp_approval', 'VP'),
                      ('hr_approval', 'HR Review'),
                      ('budget_approval', 'Budget Approval'),
                      ('final_hr_approval', 'HR Review'),
                      ('ceo_approval', 'CEO'),
                      ('finance_processing', 'Finance Processing'),
                      ('approved', 'Confirm'),
                      ('rejected', 'Rejected')]

    @api.depends('objectives_assessment_ids',
                 'performance_appraisal_policy_id')
    def _compute_total_objectives_assessment(self):
        """
        compute Total objectives assessment
        :return:
        """
        for rec in self:
            total_evaluation_value = 0.0
            evaluation_value = 0.0
            if rec.is_use_objectives:
                if rec.performance_appraisal_policy_id and \
                        rec.performance_appraisal_policy_id\
                                .objectives_out_of_evaluation:
                    for obj_line in rec.objectives_assessment_ids:
                        evaluation_value += obj_line.evaluation_value
                    if evaluation_value:
                        total_evaluation_value = \
                            evaluation_value * \
                            rec.performance_appraisal_policy_id\
                                .objectives_out_of_evaluation
            rec.total_objectives_assessment = total_evaluation_value

    @api.depends('value_assessment_ids', 'performance_appraisal_policy_id')
    def _compute_total_values_assessment(self):
        """
        compute total values assessment
        :return:
        """
        for rec in self:
            total_evaluation_value = 0.0
            evaluation_value = 0.0
            if rec.is_use_value:
                if rec.performance_appraisal_policy_id and \
                        rec.performance_appraisal_policy_id\
                                .value_out_of_evaluation:
                    for value_line in rec.value_assessment_ids:
                        evaluation_value += value_line.evaluation_value
                    if evaluation_value:
                        total_evaluation_value = \
                            evaluation_value * \
                            rec.performance_appraisal_policy_id\
                                .value_out_of_evaluation
            rec.total_values_assessment = total_evaluation_value

    @api.depends('pc_assessment_ids', 'performance_appraisal_policy_id')
    def _compute_total_pc_assessment(self):
        """
        compute total Personal Competency assessment
        :return:
        """
        for rec in self:
            total_evaluation_value = 0.0
            evaluation_value = 0.0
            if rec.is_use_personal_competencies:
                if rec.performance_appraisal_policy_id and \
                        rec.performance_appraisal_policy_id\
                                .pc_out_of_evaluation:
                    for pc_line in rec.pc_assessment_ids:
                        evaluation_value += pc_line.evaluation_value
                    if evaluation_value:
                        total_evaluation_value = \
                            evaluation_value * \
                            rec.performance_appraisal_policy_id\
                                .pc_out_of_evaluation
            rec.total_pc_assessment = total_evaluation_value

    @api.depends('pa_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.pa_submit_date:
                pa_submit_date = datetime.strptime(
                    rec.pa_submit_date, OE_DTFORMAT)
                if rec.pa_final_approval_date:
                    pa_final_approval_date = datetime.strptime(
                        rec.pa_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(pa_final_approval_date,
                                         pa_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, pa_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.pa_waiting_time = waiting_time

    @api.depends('pa_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        """
        :return:
        """
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.performance_appraisal_policy_id.sla_period or False
            sla_period_unit = \
                rec.performance_appraisal_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.pa_submit_date:
                    pa_submit_date = datetime.strptime(
                        rec.pa_submit_date, OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        pa_submit_date + _intervalTypes[
                            sla_period_unit](sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('total_objectives_assessment', 'total_values_assessment',
                 'total_pc_assessment', 'calibration')
    def _compute_final_assessment(self):
        """
        :return:
        """
        for rec in self:
            rec.final_assessment = \
                rec.total_objectives_assessment + rec.total_values_assessment \
                + rec.total_pc_assessment + rec.calibration

    name = fields.Char(string="Request Number", readonly=True, copy=False)
    description = fields.Char('Description')
    employee_id = fields.Many2one(
        'hr.employee', "Employee", required=True,
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id)], limit=1))
    employee_company_id = fields.Char(string='Employee ID', readonly=True)
    job_id = fields.Many2one('hr.job', 'Position')
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id, string='Company')
    department_id = fields.Many2one(
        'hr.department', string='Organization Unit', copy=False)
    org_unit_type = fields.Selection([
        ('root', 'Root'), ('business', 'Business Unit'),
        ('department', 'Department'), ('section', 'Section')],
        string='Organization Unit Type', copy=False)
    performance_appraisal_policy_id = fields.Many2one(
        'service.configuration.panel', string='Appraisal Performance Template')
    stage_id = fields.Many2one(
        'service.panel.displayed.states', string='States To Be Displayed',
        domain="[('service_type_ids', '=', performance_appraisal_policy_id)]",
        index=True, copy=False)
    state = fields.Selection(
        SERVICE_STATUS, string='Status', readonly=True,
        track_visibility='onchange',
        help='When the Appraisal Performance Request is created the status is '
             '\'Draft\'.\n Then the request will be forwarded based on the '
             'service type configuration.', default='draft')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', track_visibility='onchange',
        string="Cost Center")
    performance_appraisal_type = fields.Selection([
        ('quarterly', 'Quarterly'), ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly')], 'Appraisal Performance Type',
        related='performance_appraisal_policy_id.performance_appraisal_type')
    about_service = fields.Text(
        string='About The Service',
        related='performance_appraisal_policy_id.about_service')
    submit_message = fields.Text(
        related='performance_appraisal_policy_id.submit_message',
        string='Submit Hint Message', store=True)
    endorsement_text = fields.Text(
        related='performance_appraisal_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_required = fields.Boolean(
        string='Endorsement Approved', track_visibility='onchange',
        readonly=1, copy=False, states={'draft': [('readonly', False)]})
    endorsement_for_pa = fields.Boolean(
        related='performance_appraisal_policy_id.endorsement_required',
        store=True,
        string='Endorsement Required for Appraisal Performance')
    service_log_ids = fields.One2many(
        'service.log', 'performance_appraisal_id', 'Service Logs')
    is_use_objectives = fields.Boolean(
        'Use Objectives',
        related='performance_appraisal_policy_id.is_use_objectives')
    is_use_value = fields.Boolean(
        'Use Value', related='performance_appraisal_policy_id.is_use_value')
    is_use_personal_competencies = fields.Boolean(
        'Use Personal Competencies',
        related='performance_appraisal_policy_id.is_use_personal_competencies')
    review_start_date = fields.Date('Review Start Date')
    review_end_date = fields.Date('Review End Date')
    due_start_date = fields.Date('Due Start Date')
    due_end_date = fields.Date('Due End Date')
    budget = fields.Selection([
        ('under_budget', 'Under budget'),
        ('out_budget', 'Out of budget'),
        ('exceptional_out_budget', 'Out of Budget with Exception')],
        string='Budget Status')
    budget_exception_reason = fields.Text(string='Budget Exception Reason')
    input_strength = fields.Text('Strength Point/s')
    input_weaknesses = fields.Text('Weakness Point/s')
    # Appraisal Performance Assessment
    objectives_assessment_ids = fields.One2many(
        'pa.objectives.assessment', 'performance_appraisal_id',
        string='Objectives Assessment', copy=False)
    total_objectives_assessment = fields.Float(
        'Total Objectives Assessment',
        compute='_compute_total_objectives_assessment')
    value_assessment_ids = fields.One2many(
        'pa.value.assessment', 'performance_appraisal_id',
        string='Value Assessment', copy=False)
    total_values_assessment = fields.Float(
        'Total Values Assessment', compute='_compute_total_values_assessment')
    pc_assessment_ids = fields.One2many(
        'personal.competency.assessment', 'performance_appraisal_id',
        string='Personal Competency Assessment')
    total_pc_assessment = fields.Float(
        'Total Personal Competency Assessment',
        compute='_compute_total_pc_assessment')
    calibration = fields.Float('Calibration(-/+)')
    final_assessment = fields.Float('Final Assessment', compute='_compute_final_assessment')
    # approvals
    pa_submitted_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True, copy=False,
        help='Who requested the service.')
    pa_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                     copy=False)
    pa_manager_user_id = fields.Many2one(
        'res.users', string='Manager Approval', readonly=True, copy=False)
    pa_manager_approval_date = fields.Datetime(
        string='Manager Approval Date', readonly=True, copy=False)
    pa_vp_user_id = fields.Many2one(
        'res.users', string='VP Approval', readonly=True, copy=False)
    pa_vp_approval_date = fields.Datetime(
        string='VP Approval Date', readonly=True, copy=False)
    pa_hr_user_id = fields.Many2one(
        'res.users', string='HR Approval', readonly=True, copy=False)
    pa_hr_approval_date = fields.Datetime(
        string='HR Approval Date', readonly=True, copy=False)
    pa_ceo_user_id = fields.Many2one(
        'res.users', string='CEO Approval', readonly=True, copy=False)
    pa_ceo_approval_date = fields.Datetime(
        string='CEO Approval Date', readonly=True, copy=False)
    pa_finance_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    pa_finance_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    pa_final_approval_date = fields.Datetime(
        'Final Approval Date', readonly=True, copy=False)
    pa_waiting_time = fields.Char(
        compute=_calculate_ongoing_waiting_time,
        string='Waiting Time', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA', method=True, copy=False,
        states={'draft': [('readonly', False)]}, store=True)

    # Accounting Information

    # Details

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id and self.company_id.performance_appraisal_policy_id:
            self.performance_appraisal_policy_id = \
                self.company_id.performance_appraisal_policy_id.id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        Onchange Employee Id
        :return:
        """
        if self.employee_id:
            self.employee_company_id = self.employee_id.f_employee_no
            self.job_id = self.employee_id.job_id and \
                          self.employee_id.job_id or False
            self.department_id = self.employee_id.department_id and \
                                 self.employee_id.department_id.id or False
            self.org_unit_type = self.employee_id.department_id and \
                                 self.employee_id.department_id.org_unit_type
            self.account_analytic_id = self.job_id and \
                                       self.job_id.analytic_account_id or False

    @api.multi
    def update_assessment(self):
        """
        update Objectives, value
        :return:
        """
        for rec in self:
            if rec.performance_appraisal_policy_id:
                # Update Objectives
                if rec.is_use_objectives:
                    for obj_rec in self.env['pa.objectives'].search([
                        ('locked_by_hr', '=', True),
                        ('status', '!=', 'closed')]):
                        self.env['pa.objectives.assessment'].create({
                            'goal': obj_rec.goal,
                            'weightage': obj_rec.weightage,
                            'measurement': obj_rec.measurement,
                            'target_date': obj_rec.target_date,
                            'actual_date': obj_rec.actual_date,
                            'completed': obj_rec.completed,
                            'status': obj_rec.status,
                            'performance_appraisal_id': rec.id,
                        })
                # Update Value
                if rec.is_use_value and \
                        rec.performance_appraisal_policy_id.is_use_value:
                    for value_rec in \
                            rec.performance_appraisal_policy_id.pa_value_ids:
                        self.env['pa.value.assessment'].create({
                            'name': value_rec.name,
                            'description': value_rec.description,
                            'performance_appraisal_id': self.id,
                        })
                # Update Personal Competencies
                if rec.is_use_personal_competencies and \
                        rec.performance_appraisal_policy_id.\
                                is_use_personal_competencies:
                    for pc_rec in \
                            rec.performance_appraisal_policy_id.personal_competency_ids:
                        self.env['personal.competency.assessment'].create({
                            'name': pc_rec.name,
                            'description': pc_rec.description,
                            'performance_appraisal_id': self.id,
                        })

    @api.onchange('performance_appraisal_policy_id')
    def onchange_performance_appraisal_policy_id(self):
        """
        :return: onchange appraisal performance.
        """
        if self.performance_appraisal_policy_id:
            # Update Stages
            if self.performance_appraisal_policy_id.states_to_display_ids:
                stage_rec = \
                    self.performance_appraisal_policy_id.states_to_display_ids[
                        0]
                stage_list = filter(None, map(
                    lambda x: x.case_default and x,
                    self.performance_appraisal_policy_id.states_to_display_ids
                ))
                if stage_list:
                    stage_rec = stage_list[0]
                self.stage_id = stage_rec.id

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'performance.appraisal')
        res = super(PerformanceAppraisal, self).create(vals)
        return res

    # common methods for all buttons
    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _get_service_req_approvals(self):
        """
        This list must be in the same workflow states order to help in
        identifying/tracking the states (previous and destination).
        :return:
        """
        req_approvals = []
        for service in self:
            if service.performance_appraisal_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.performance_appraisal_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.performance_appraisal_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.performance_appraisal_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.performance_appraisal_policy_id.hr_approval:
            #     req_approvals.append('final_hr_approval')
            # if service.performance_appraisal_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
            if service.performance_appraisal_policy_id.finance_approval:
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
        elif self.is_transition_allowed('budget_approval'):
            self.action_submit_to_budget_approval()
        # elif self.is_transition_allowed('final_hr_approval'):
        #     self.action_submit_to_hr_review()
        elif self.is_transition_allowed('ceo_approval'):
            self.action_submit_to_ceo_approval()
        elif self.is_transition_allowed('finance_processing'):
            self.action_submit_to_final_finance_processing()
        else:
            return False
        return True

    @api.multi
    def _get_appraisal_performance_dest_state(self, service):
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
    def _check_appraisal_performance_restrictions(self):
        for service in self:
            # ir_obj = self.env['ir.attachment']
            # attachment_mandatory = \
            #     service.performance_appraisal_policy_id.attachment_mandatory
            # if attachment_mandatory:
            #     existing_attachment = ir_obj.search([
            #         ('res_id', '=', service.id),
            #         ('res_model', '=', service._name)])
            #     if not existing_attachment:
            #         raise Warning(
            #             _('You are not allowed to submit the request without '
            #               'attaching a document.\n For attaching a document: '
            #               'press save then attach a document.'))
            if service.performance_appraisal_policy_id.endorsement_required \
                    and not service.endorsement_required:
                raise Warning(
                    _("To proceed, Kindly agree on the endorsement."))

    @api.model
    def _get_dest_related_stages(self, dest_state):
        """
        get destination stages
        :return:
        """
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'performance.appraisal')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.model
    def _get_appraisal_performance_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_dest_related_stages(dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for %s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'pa_submitted_by': self.env.user.id,
                           'pa_submit_date': self._get_current_datetime()})
        elif current_state == 'mngr_approval':
            result.update(
                {'state': dest_state,
                 'pa_manager_user_id': self.env.user.id,
                 'pa_manager_approval_date': self._get_current_datetime()})
        elif current_state == 'vp_approval':
            result.update(
                {'state': dest_state,
                 'pa_vp_user_id': self.env.user.id,
                 'pa_vp_approval_date': self._get_current_datetime()})
        elif current_state == 'hr_approval':
            result.update(
                {'state': dest_state,
                 'pa_hr_user_id': self.env.user.id,
                 'pa_hr_approval_date': self._get_current_datetime()})
        elif current_state == 'budget_approval':
            result.update(
                {'state': dest_state,
                 'bt_budget_user_id': self.env.user.id,
                 'bt_budget_approval_date': self._get_current_datetime()})
        elif current_state == 'ceo_approval':
            result.update(
                {'state': dest_state,
                 'pa_ceo_user_id': self.env.user.id,
                 'pa_ceo_approval_date': self._get_current_datetime()})
        elif current_state == 'finance_processing':
            result.update(
                {'state': dest_state,
                 'pa_finance_user_id': self.env.user.id,
                 'pa_finance_approval_date': self._get_current_datetime()})
        elif current_state == 'rejected':
            result.update({'state': dest_state})
        elif current_state == 'locked':
            result.update({'state': dest_state})

        return result

    # Button Action
    @api.multi
    def action_submit_request(self):
        """
        :return:
        """
        for rec in self:
            if not rec.performance_appraisal_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the appraisal performance policy has been '
                      'applied.'))
            rec._check_point_for_all_stage()

    @api.multi
    def action_submit_to_manager(self):
        for service in self:
            self._check_appraisal_performance_restrictions()
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                service.write(
                    self._get_appraisal_performance_approval_info(
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
            self._check_appraisal_performance_restrictions()
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                self.write(
                    self._get_appraisal_performance_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_approval(self):
        """
        VP Approval
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                self.write(
                    self._get_appraisal_performance_approval_info(
                        service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_budget_approval(self):
        """
        Hr Approved
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                self.write(
                    self._get_appraisal_performance_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_review(self):
        """
        Budget Approved
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            if service.budget:
                if service.budget == 'out_budget':
                    raise Warning(_("You cannot proceed with this request "
                                    "because it's out of budget. "))
            else:
                raise Warning(
                    _("You cannot proceed without budget status. "))
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                self.write(
                    self._get_appraisal_performance_approval_info(
                        service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_finance_processing(self):
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = self._get_appraisal_performance_dest_state(service)
            if dest_state:
                self.write(
                    self._get_appraisal_performance_approval_info(service,
                                                          dest_state))
                self._action_send_email(dest_state)
        return True

    # Reject & Return
    @api.multi
    def action_appraisal_performance_reject(self):
        """
        return appraisal performance reject
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = 'rejected'
            service.write(self._get_appraisal_performance_approval_info(
                service, dest_state))
            self._action_send_email('rejected')

    @api.multi
    def action_appraisal_performance_return(self):
        """
        return appraisal performance request
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = 'draft'
            result = self._get_appraisal_performance_approval_info(
                service, dest_state)
            # result.update(self._get_return_dict())
            service.write(result)
            self._action_send_email('return_to_draft')
        return True

    @api.multi
    def calibration_by_vp(self):
        """
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_appraisal_performance_restrictions()
            dest_state = 'mngr_approval'
            result = self._get_appraisal_performance_approval_info(
                service, dest_state)
            service.write(result)
            self.with_context({
                'reason': self._context.get('reason')})._action_send_email(
                'calibration_by_vp')
        return True

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
            'org_performance_appraisal.performance_appraisal_req_action_view'
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
            'model': 'performance.appraisal'
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
            temp_xml_id = \
                'org_performance_appraisal.pa_request_send_to_manager'
        elif dest_state == 'vp_approval':
            temp_xml_id = 'org_performance_appraisal.pa_request_send_to_vp'
        elif dest_state == 'hr_approval':
            temp_xml_id = \
                'org_performance_appraisal.pa_request_send_to_hr_approval'
        elif dest_state == 'ceo_approval':
            temp_xml_id = 'org_performance_appraisal.pa_request_send_to_ceo'
        elif dest_state == 'finance_processing':
            temp_xml_id = 'org_performance_appraisal.' \
                          'pa_request_send_to_final_finance_processing'
        elif dest_state == 'approved':
            temp_xml_id = 'org_performance_appraisal.pa_request_approved'
        elif dest_state == 'return_to_draft':
            temp_xml_id = 'org_performance_appraisal.pa_request_return'
        elif dest_state == 'calibration_by_vp':
            temp_xml_id = 'org_performance_appraisal.' \
                          'vp_calibration_pa_request_send_to_manager'
        elif dest_state == 'rejected':
            temp_xml_id = 'org_performance_appraisal.pa_request_rejected'
        elif dest_state == 'locked':
            temp_xml_id = 'org_performance_appraisal.pa_request_locked'
        elif dest_state == 'unlocked':
            temp_xml_id = 'org_performance_appraisal.pa_request_unlocked'

        if temp_xml_id:
            self._send_email(temp_xml_id, email_to)
        return True
