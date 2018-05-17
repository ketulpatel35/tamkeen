from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from dateutil.relativedelta import relativedelta

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class OrgBenefitsProgram(models.Model):
    _name = 'org.benefits.program'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Benefits Program'
    _order = 'name desc'

    SERVICE_STATUS = [('draft', 'To Submit'),
                      ('mngr_approval', 'Direct Manager'),
                      ('vp_approval', 'VP'),
                      ('ceo_approval', 'CEO'),
                      ('hr_approval', 'HR Review'),
                      ('finance_processing', 'Finance Processing'),
                      ('final_hr_approval', 'HR Review'),
                      ('approved', 'Confirm'),
                      ('rejected', 'Rejected'),
                      ('locked', 'Locked')]

    @api.depends('bp_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.bp_submit_date:
                bp_submit_date = datetime.strptime(
                    rec.bp_submit_date, OE_DTFORMAT)
                if rec.bp_final_approval_date:
                    bp_final_approval_date = datetime.strptime(
                        rec.bp_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(bp_final_approval_date,
                                         bp_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, bp_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.bp_waiting_time = waiting_time

    @api.depends('bp_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        """
        :return:
        """
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.benefits_program_policy_id.sla_period or False
            sla_period_unit = \
                rec.benefits_program_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.bp_submit_date:
                    bp_submit_date = datetime.strptime(
                        rec.bp_submit_date, OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        bp_submit_date + _intervalTypes[
                            sla_period_unit](sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('bp_sub_benefits_ids', 'bp_dependents_ids',
                 'benefits_program_policy_id')
    def _calculation_total_benefits(self):
        """
        calculates total amount of sub benefits
        :return:
        """
        for rec in self:
            total = 0
            if rec.is_display_sub_benefits:
                for sub_benefits_rec in rec.bp_sub_benefits_ids:
                    total += sub_benefits_rec.amount
            elif rec.is_display_dependents:
                for dependents_rec in rec.bp_dependents_ids:
                    total += dependents_rec.total_fees
            rec.total_benefit = total

    name = fields.Char(string="Request Number", readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', "Employee", required=True,
                                  default=lambda self: self.
                                  env['hr.employee'].search([
                                      ('user_id', '=', self.env.user.id)],
                                      limit=1))
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
    benefits_program_policy_id = fields.Many2one(
        'service.configuration.panel', string='Benefits Program Type')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', track_visibility='onchange',
        string="Cost Center")
    about_service = fields.Text(
        string='About The Service',
        related='benefits_program_policy_id.about_service')
    submit_message = fields.Text(
        related='benefits_program_policy_id.submit_message',
        string='Submit Hint Message', store=True)
    stage_id = fields.Many2one(
        'service.panel.displayed.states', string='States To Be Displayed',
        domain="[('service_type_ids', '=', benefits_program_policy_id)]",
        index=True, copy=False)
    state = fields.Selection(
        SERVICE_STATUS, string='Status', readonly=True,
        track_visibility='onchange',
        help='When the Benefits Program Request is created the status is '
             '\'Draft\'.\n Then the request will be forwarded based on the '
             'service type configuration.', default='draft')
    endorsement_text = fields.Text(
        related='benefits_program_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_required = fields.Boolean(
        string='Endorsement Approved', track_visibility='onchange',
        readonly=1, copy=False, states={'draft': [('readonly', False)]})
    endorsement_for_bp = fields.Boolean(
        related='benefits_program_policy_id.endorsement_required',
        store=True,
        string='Endorsement Required for Benefits Program')
    # approvals
    bp_submitted_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True, copy=False,
        help='Who requested the service.')
    bp_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                     copy=False)
    bp_manager_user_id = fields.Many2one(
        'res.users', string='Manager Approval', readonly=True, copy=False)
    bp_manager_approval_date = fields.Datetime(
        string='Manager Approval Date', readonly=True, copy=False)
    bp_vp_user_id = fields.Many2one(
        'res.users', string='VP Approval', readonly=True, copy=False)
    bp_vp_approval_date = fields.Datetime(
        string='VP Approval Date', readonly=True, copy=False)
    bp_hr_user_id = fields.Many2one(
        'res.users', string='HR Approval', readonly=True, copy=False)
    bp_hr_approval_date = fields.Datetime(
        string='HR Approval Date', readonly=True, copy=False)
    bp_ceo_user_id = fields.Many2one(
        'res.users', string='CEO Approval', readonly=True, copy=False)
    bp_ceo_approval_date = fields.Datetime(
        string='CEO Approval Date', readonly=True, copy=False)
    bp_finance_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    bp_finance_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    bp_rejected_user_id = fields.Many2one(
        'res.users', string='Rejected By', readonly=True, copy=False)
    bp_rejected_date = fields.Datetime(
        string='Rejected Date', readonly=True, copy=False)
    bp_final_approval_date = fields.Datetime(
        'Final Approval Date', readonly=True, copy=False)
    bp_waiting_time = fields.Char(
        compute=_calculate_ongoing_waiting_time,
        string='Waiting Time', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA', method=True, copy=False,
        states={'draft': [('readonly', False)]}, store=True)
    service_log_ids = fields.One2many('service.log', 'benefits_program_id',
                                      'Service Logs')
    # Accounting Information
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    accounting_date = fields.Date(string='Accounting Date', copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 copy=False)
    debit_account_id = fields.Many2one('account.account',
                                       string='Debit Account', copy=False)
    credit_account_id = fields.Many2one('account.account',
                                        string='Credit Account', copy=False)
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
                                      copy=False)
    paid_to_employee = fields.Boolean(string='Paid to Employee', copy=False)
    product_id = fields.Many2one('product.product', string='Product')

    # Details
    is_display_sub_benefits = fields.Boolean(
        related='benefits_program_policy_id.is_display_sub_benefits',
        store=True, string='Display Sub-Benefits')
    is_display_dependents = fields.Boolean(
        related='benefits_program_policy_id.is_display_dependents',
        store=True, string='Display Sub-Benefits')
    bp_dependents_ids = fields.One2many(
        'benefits.program.dependents', 'benefits_program_id', 'Dependents')
    bp_sub_benefits_ids = fields.One2many(
        'org.sub.benefits.program', 'benefits_program_id', 'Sub Benefits')
    total_benefit = fields.Float(
        'Request Total Value', compute='_calculation_total_benefits',
        store=True)
    allocated_budget = fields.Float('Total Allocated Budget')
    remain_allocated_budget = fields.Float('Total Remaining Value')
    pre_requested_total_value = fields.Float('Pre-Requested Total Value')
    calendar_year = fields.Char('Calendar Year', default=datetime.today().year)
    proof_required = fields.Boolean(
        related='benefits_program_policy_id.proof_required',
        string='Proof Required', store=True)
    benefits_proof_ids = fields.One2many(
        'benefits.proof', 'benefits_program_id', string='Attachment/s')

    @api.model
    def get_balance_from_employee_contract(self, benefits_type):
        """
        get balance from employee contract
        :return:
        """
        balance = 'False'
        if self.employee_id and self.employee_id.contract_id and \
                self.employee_id.contract_id.entitled_manual_benefits:
            if benefits_type == 'education':
                balance = self.employee_id.contract_id.education_benefit
            elif benefits_type == 'flexible':
                balance = self.employee_id.contract_id.flexible_benefit
            elif benefits_type == 'wellness':
                balance = self.employee_id.contract_id.wellness_program
            else:
                balance = 0.0
        return balance

    def _get_amount_localdict(self, employee_rec):
        blacklist = []

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict,
                                                      category.parent_id,
                                                      amount)
            localdict[
                'categories'].dict[category.code] = \
                category.code in localdict['categories'].dict and \
                localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):

            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        rules_dict = {}
        current_rule_ids = []
        if employee_rec.contract_id.struct_id:
            contract_struct_rec = employee_rec.contract_id.struct_id \
                ._get_parent_structure()
            for struct in contract_struct_rec:
                sort_current_rule_ids = struct.rule_ids.ids
                current_rule_ids += list(set(sort_current_rule_ids))
        categories = BrowsableObject(employee_rec.id, {}, self.env)
        rules = BrowsableObject(employee_rec.id, rules_dict, self.env)
        baselocaldict = {'categories': categories, 'rules': rules}

        structure_rec = self.env['hr.payroll.structure'].search([('code',
                                                                  '=',
                                                                  'LCSS')])
        # structure_rec = structure_lcss._get_parent_structure()
        rule_ids = structure_rec.get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids,
                                                         key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
        localdict = dict(baselocaldict, employee=employee_rec,
                         contract=employee_rec.contract_id)
        count = 0
        for rule in sorted_rules:
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            localdict['result_rate'] = 100
            if rule.satisfy_condition(localdict) and rule.id not in \
                    blacklist and rule.id in current_rule_ids:
                # compute the amount of the rule
                amount, qty, rate = rule.compute_rule(localdict)
                count += amount
                # check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[
                    rule.code] or 0.0
                # set/overwrite the amount computed for this rule in the
                # localdict
                tot_rule = amount * qty * rate / 100.0
                # if localdict.get(rule.code):
                #     tot_rule += localdict.get(rule.code)
                localdict[rule.code] = tot_rule
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = _sum_salary_rule_category(localdict,
                                                      rule.category_id,
                                                      tot_rule -
                                                      previous_amount)
        return localdict

    @api.model
    def get_balance_from_configuration(self):
        """
        get balance from configuration
        :param benefits_type:
        :return:
        """
        if self.employee_id.contract_id and \
                self.employee_id.contract_id.grade_level:
            for cal_rec in \
                    self.benefits_program_policy_id.bp_calculation_config_ids:
                if self.employee_id.contract_id.grade_level.id in \
                        cal_rec.grade_level_ids.ids:
                    localdict = self._get_amount_localdict(self.employee_id)
                    amount_tuple = cal_rec.computation_rule.compute_rule(
                        localdict)
                    return amount_tuple[0]
        return 0.0

    @api.model
    def get_allocated_budget(self):
        """
        get allocated budget
        :return:
        """
        benefits_type = ''
        if self.is_display_sub_benefits:
            if self.benefits_program_policy_id.code == 'WLNSPRGM':
                benefits_type = 'wellness'
            if self.benefits_program_policy_id.code == 'FLXBNFT':
                benefits_type = 'flexible'
        elif self.is_display_dependents and \
                        self.benefits_program_policy_id.code == 'EDUDNFT':
            benefits_type = 'education'
        allocated_budget = self.get_balance_from_employee_contract(
            benefits_type)
        if allocated_budget == 'False':
            allocated_budget = self.get_balance_from_configuration()
        return allocated_budget

    def _get_old_benefit_program_rec(self):
        benefit_program_type_list = ['EDUDNFT', 'FLXBNFT']
        domain = [('state', 'not in', ['rejected']),
                  ('calendar_year', '=', str(datetime.today().year)),
                  ('employee_id', '=', self.employee_id.id)]
        if self.benefits_program_policy_id.code in benefit_program_type_list \
                and self.employee_id.contract_id and \
                self.employee_id.contract_id.grade_level and \
                self.employee_id.contract_id.grade_level. \
                        education_flexible_one_budget:
            domain.append(('benefits_program_policy_id.code', 'in',
                           benefit_program_type_list))
        else:
            domain.append(('benefits_program_policy_id', '=',
                           self.benefits_program_policy_id.id))
        old_rec = self.search(domain)
        return old_rec

    def _get_old_benefit_program_for_type_rec(self):
        old_rec = self.search([
            ('state', 'not in', ['rejected']),
            ('calendar_year', '=', str(datetime.today().year)),
            ('employee_id', '=', self.employee_id.id),
            ('benefits_program_policy_id.code', 'in', ('FLXBNFT',
                                                       'EDUDNFT')),
            ('id', '!=', self.id)
        ], limit=1, order="id desc")
        return old_rec

    def _check_benefit_program_code(self):
        if self.benefits_program_policy_id.code and self.employee_id and \
                self.employee_id.contract_id and \
                self.employee_id.contract_id.grade_level and \
                not self.employee_id.contract_id.grade_level \
                        .education_flexible_one_budget:
            code = self.benefits_program_policy_id.code
            old_rec = self._get_old_benefit_program_for_type_rec()
            if not old_rec:
                return True
            else:
                if old_rec.benefits_program_policy_id:
                    old_rec_code = old_rec.benefits_program_policy_id.code
                    if code != old_rec_code:
                        return False
        return True

    def _get_name_for_edu_flexible_benefit(self):
        service_panel_obj = self.env['service.configuration.panel']
        education_name, flexible_name = '', ''
        education_rec = service_panel_obj.search([('code', '=',
                                                   ('EDUDNFT'))], limit=1)
        flexible_rec = service_panel_obj.search([('code', '=',
                                                  ('FLXBNFT'))], limit=1)
        if education_rec:
            education_name = education_rec.name
        if flexible_rec:
            flexible_name = flexible_rec.name
        return education_name, flexible_name

    def _check_education_flexible_budget(self):
        benefit_program_type_list = ['EDUDNFT', 'FLXBNFT']
        if self.benefits_program_policy_id.code in \
                benefit_program_type_list:
            if not self._check_benefit_program_code():
                education_name, flexible_name = \
                    self._get_name_for_edu_flexible_benefit()
                raise Warning(_('As per the company policy you are allowed '
                                'to request either %s or %s within the '
                                'current '
                                'year.') % (education_name, flexible_name))
        return True

    def get_allocated_budget_till_now(self):
        """
        Calculate allocated budget till now
        :return:
        """
        total_used_budget = 0.0
        # self._check_education_flexible_budget()
        if self.employee_id and self.benefits_program_policy_id and \
                self.allocated_budget:
            for old_rec in self._get_old_benefit_program_rec():
                if self._origin.id == old_rec.id:
                    continue
                total_used_budget += old_rec.total_benefit
                # old_rec_program_lst.append(
                #     old_rec.benefits_program_policy_id.code)
        return total_used_budget

    @api.model
    def update_benefits_related_values(self):
        """
        update related fields on onchange value of
        benefits_program_policy_id and total_benefit
        :return:
        """
        self.allocated_budget = self.get_allocated_budget()
        allocated_budget_till_now = self.get_allocated_budget_till_now()
        self.pre_requested_total_value = allocated_budget_till_now
        self.remain_allocated_budget = self.allocated_budget - (
            self.pre_requested_total_value + self.total_benefit)

    @api.onchange('total_benefit')
    def onchange_total_benefit(self):
        """
        :return:
        """
        self.update_benefits_related_values()

    @api.model
    def update_account_information(self):
        """
        :return:
        """
        if self.benefits_program_policy_id:
            self.product_id = self.benefits_program_policy_id.product_id and \
                              self.benefits_program_policy_id.product_id.id or False
            self.journal_id = self.benefits_program_policy_id.journal_id and \
                              self.benefits_program_policy_id.journal_id.id or False
            self.credit_account_id = \
                self.benefits_program_policy_id.journal_id and \
                self.benefits_program_policy_id.journal_id \
                    .default_credit_account_id or False
            self.debit_account_id = \
                self.benefits_program_policy_id.product_id and \
                self.benefits_program_policy_id.product_id. \
                    property_account_expense_id or False

    @api.onchange('benefits_program_policy_id')
    def onchange_benefits_program_policy(self):
        """
        :return: onchange Benefits Program.
        """
        if self.benefits_program_policy_id:
            if self.benefits_program_policy_id.states_to_display_ids:
                stage_rec = \
                    self.benefits_program_policy_id.states_to_display_ids[0]
                stage_list = filter(None, map(
                    lambda x: x.case_default and x,
                    self.benefits_program_policy_id.states_to_display_ids))
                if stage_list:
                    stage_rec = stage_list[0]
                self.stage_id = stage_rec.id
            # account information
            self.update_account_information()
            # proof required
            proof_lst = []
            if self.proof_required:
                for proof_rec in self.benefits_proof_ids:
                    proof_lst.append((2, proof_rec.id))
                for line in self.benefits_program_policy_id.service_proof_ids:
                    proof_lst.append((0, 0, {
                        'name': line.name, 'description': line.description,
                        'mandatory': line.mandatory
                    }))
                self.benefits_proof_ids = proof_lst
            self.update_benefits_related_values()
            # remove unknown data
            dependents_lst = []
            [dependents_lst.append((2, d_rec.id)) for d_rec in
             self.bp_dependents_ids]
            self.bp_dependents_ids = dependents_lst
            benefits_lst = []
            [benefits_lst.append((2, b_rec.id)) for b_rec in
             self.bp_sub_benefits_ids]
            self.bp_sub_benefits_ids = benefits_lst

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id and self.company_id.benefits_program_policy_id:
            self.benefits_program_policy_id = \
                self.company_id.benefits_program_policy_id.id

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
            self.onchange_benefits_program_policy()

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'benefits.program')
        res = super(OrgBenefitsProgram, self).create(vals)
        return res

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if self.benefits_program_policy_id and \
                self.benefits_program_policy_id.states_to_display_ids:
            stage_rec = self.benefits_program_policy_id.states_to_display_ids[
                0]
            stage_list = filter(None, map(
                lambda x: x.case_default and x,
                self.benefits_program_policy_id.states_to_display_ids))
            if stage_list:
                stage_rec = stage_list[0]
            self.stage_id = stage_rec.id
        default.update({'stage_id': stage_rec.id})
        return super(OrgBenefitsProgram, self).copy(default)

    # common methods for all buttons
    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.multi
    def _check_user_permissions(self, sign='approve'):
        for rec in self:
            if not rec._check_group(
                    'org_benefits_program.group_bp_self_approval_service'):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(_(
                        "Please, Make sure that you have the rights to %s "
                        "your own request.") % (sign))
        return False

    @api.multi
    def _get_service_req_approvals(self):
        """
        This list must be in the same workflow states order to help in
        identifying/tracking the states (previous and destination).
        :return:
        """
        req_approvals = []
        for service in self:
            if service.benefits_program_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.benefits_program_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.benefits_program_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.benefits_program_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
            if service.benefits_program_policy_id.finance_approval:
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
        elif self.is_transition_allowed('finance_processing'):
            self.action_submit_to_final_finance_processing()
        else:
            return False
        return True

    @api.multi
    def _get_benefits_program_dest_state(self, service):
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
    def _check_benefits_program_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.benefits_program_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachment = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachment:
                    raise Warning(
                        _('You are not allowed to submit the request without '
                          'attaching a document.\n For attaching a document: '
                          'press save then attach a document.'))
            if service.benefits_program_policy_id.endorsement_required and not \
                    service.endorsement_required:
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
            ('model_id.model', '=', 'org.benefits.program')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.model
    def _get_benefit_program_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_dest_related_stages(dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for %s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'bp_submitted_by': self.env.user.id,
                           'bp_submit_date': self._get_current_datetime()})
        elif current_state == 'mngr_approval':
            result.update(
                {'state': dest_state,
                 'bp_manager_user_id': self.env.user.id,
                 'bp_manager_approval_date': self._get_current_datetime()})
        elif current_state == 'vp_approval':
            result.update(
                {'state': dest_state,
                 'bp_vp_user_id': self.env.user.id,
                 'bp_vp_approval_date': self._get_current_datetime()})
        elif current_state == 'hr_approval':
            result.update(
                {'state': dest_state,
                 'bp_hr_user_id': self.env.user.id,
                 'bp_hr_approval_date': self._get_current_datetime()})
        elif current_state == 'ceo_approval':
            result.update(
                {'state': dest_state,
                 'bp_ceo_user_id': self.env.user.id,
                 'bp_ceo_approval_date': self._get_current_datetime()})
        elif current_state == 'finance_processing':
            result.update(
                {'state': dest_state,
                 'bp_finance_user_id': self.env.user.id,
                 'bp_finance_approval_date': self._get_current_datetime()})
        elif current_state == 'rejected':
            result.update({'state': dest_state})
        elif current_state == 'locked':
            result.update({'state': dest_state})

        return result

    # Buttons Actions
    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    @api.model
    def check_for_service_proof(self):
        """
        :return:
        """
        for rec in self.benefits_proof_ids:
            if rec.mandatory and not rec.document:
                raise Warning(
                    _('To proceed,'
                      'Kindly you should attach the files as required '
                      'in the service.'))

    @api.multi
    def action_submit_request(self):
        """
        submit Benefits Program request
        :return:
        """
        for rec in self:
            if not rec.benefits_program_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the benefits policy has been applied.'))
            self._check_education_flexible_budget()
            allow_behalf_req = rec._check_group(
                'org_benefits_program.group_bp_on_behalf_of_other')
            if not allow_behalf_req:
                employee_rec = self.env['hr.employee'].search(
                    [('user_id', '=', self._uid)], limit=1)
                if self.employee_id != employee_rec:
                    raise Warning(_('You are not allowed to do this change on '
                                    'behalf of others.'))
            rec.check_for_service_proof()
            rec._check_benefits_program_restrictions()
            rec._check_budget_restriction()
            rec._check_point_for_all_stage()

    @api.model
    def get_child_allocated_balance(self):
        """
        :return:
        """
        child_dict = {}
        [child_dict.update({x: 0.0}) for x in self.env[
            'employee.family.info'].search([
            ('employee_id', '=', self.employee_id.id),
            ('relationship', 'in', ['son', 'daughter']),
            ('age', '>=', '5'), ('age', '<=', '18')])]
        for rec in self.search([
            ('state', 'not in', ['rejected']),
            ('calendar_year', '=', str(datetime.today().year)),
            ('employee_id', '=', self.employee_id.id),
            ('benefits_program_policy_id', '=',
             self.benefits_program_policy_id.id),
            ('is_display_dependents', '=', True)]):
            for dependents_rec in rec.bp_dependents_ids:
                if dependents_rec.child_id in child_dict:
                    child_dict[dependents_rec.child_id] += \
                        dependents_rec.total_fees
        return child_dict

    @api.model
    def check_dependents_validation(self):
        """
        check number of dependent allow
        :return:
        """
        max_dep = self.benefits_program_policy_id.allow_maximum_dependents
        dependents_list = []
        for dependents_rec in self.bp_dependents_ids:
            if dependents_rec.age < \
                    self.benefits_program_policy_id.allow_min_age or \
                            dependents_rec.age > \
                            self.benefits_program_policy_id.allow_max_age:
                raise Warning(_(
                    'You are not eligible to claim the expenses of %s since '
                    'the age not between %s to %s.') % (
                                  dependents_rec.child_id.name,
                                  self.benefits_program_policy_id.allow_min_age,
                                  self.benefits_program_policy_id.allow_max_age))
            if dependents_rec.child_id.id not in dependents_list:
                dependents_list.append(dependents_rec.child_id.id)
        
        if self.employee_id.children_age_5_18 > 1:
            if self.employee_id.contract_id and \
                    self.employee_id.contract_id.grade_level:
                if not self.employee_id.contract_id.grade_level \
                            .education_flexible_one_budget:
                    each_child_allocation = 0
                    if len(dependents_list) > max_dep:
                        raise Warning(
                            _('You are eligible only for adding the expenses '
                              'of %s children.') % (max_dep))
                    allow_child = self.employee_id.children_age_5_18
                    if allow_child > max_dep:
                        allow_child = max_dep
                        if max_dep > 0 and allow_child > 0:
                            each_child_allocation = \
                                self.allocated_budget / allow_child
                    child_dict = self.get_child_allocated_balance()
                    for key in child_dict:
                        if child_dict[key] > each_child_allocation:
                            raise Warning(_('The allowed budget per child is %s, '
                                            'Kindly check (%s) request.') % (
                                each_child_allocation, key.name))
            else:
                raise Warning(_('Kindly, Contact the HR team to check your compensation profile.'))

    @api.model
    def _check_budget_restriction(self):
        """
        check budget restriction
        :return:
        """
        if self.total_benefit <= 0:
            raise Warning(_('No request with 0 value is allowed to be '
                            'submitted.'))
        if self.benefits_program_policy_id:
            if not self.allocated_budget:
                raise Warning(_('There is no allocated budget,'
                                'Kindly check with the HR department.'))
            rem_val = self.allocated_budget - self.pre_requested_total_value
            if self.remain_allocated_budget < 0:
                raise Warning(_(
                    'As per the allocated budget for such benefits, '
                    'You are eligible only for '
                    '%s %s.') % (rem_val, self.currency_id.symbol))
            if self.is_display_dependents:
                self.check_dependents_validation()

    @api.multi
    def action_submit_to_manager(self):
        for service in self:
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self._check_budget_restriction()
                service.write(
                    self._get_benefit_program_approval_info(
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
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(
                    self._get_benefit_program_approval_info(service,
                                                            dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_approval(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(
                    self._get_benefit_program_approval_info(service,
                                                            dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_ceo_approval(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(
                    self._get_benefit_program_approval_info(service,
                                                            dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_finance_processing(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(
                    self._get_benefit_program_approval_info(service,
                                                            dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_final_finance_processing(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(
                    self._get_benefit_program_approval_info(service,
                                                            dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_final_hr_approved(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_benefits_program_restrictions()
            dest_state = self._get_benefits_program_dest_state(service)
            if dest_state:
                self.write(self._get_benefit_program_approval_info(
                    service, dest_state))
                self.write({
                    'bp_final_approval_date': self._get_current_datetime()
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
            'bp_submitted_by': False,
            'bp_submit_date': False,
            'bp_manager_user_id': False,
            'bp_manager_approval_date': False,
            'bp_vp_user_id': False,
            'bp_vp_approval_date': False,
            'bp_hr_user_id': False,
            'bp_hr_approval_date': False,
            'bp_ceo_user_id': False,
            'bp_ceo_approval_date': False,
            'bp_finance_user_id': False,
            'bp_finance_approval_date': False,
            'bp_rejected_user_id': False,
            'bp_rejected_date': False,
            'bp_final_approval_date': False,
        }
        return return_dict

    @api.multi
    def action_benefit_program_return(self):
        """
        return benefits program request
        :return:
        """
        for service in self:
            self._check_benefits_program_restrictions()
            dest_state = 'draft'
            result = self._get_benefit_program_approval_info(
                service, dest_state)
            result.update(self._get_return_dict())
            service.write(result)
            self._action_send_email('return_to_draft')
        return True

    @api.multi
    def action_benefit_program_reject(self):
        """
        return benefits program reject
        :return:
        """
        for service in self:
            self._check_user_permissions('reject')
            self._check_benefits_program_restrictions()
            dest_state = 'rejected'
            service.write(self._get_benefit_program_approval_info(
                service, dest_state))
            self._action_send_email('rejected')

    @api.multi
    def action_benefit_program_lock(self):
        """
        Lock benefit program
        :return:
        """
        for service in self:
            self._check_user_permissions('lock')
            self._check_benefits_program_restrictions()
            dest_state = 'locked'
            service.write(self._get_benefit_program_approval_info(
                service, dest_state))
            self._action_send_email('locked')

    @api.multi
    def action_benefit_program_unlock(self):
        """
        Lock benefit program
        :return:
        """
        for service in self:
            self._check_user_permissions('unlock')
            self._check_benefits_program_restrictions()
            dest_state = 'hr_approval'
            service.write(self._get_benefit_program_approval_info(
                service, dest_state))
            self._action_send_email('unlocked')

    def _prepare_move_lines(self, move):
        move_lst = []
        name = self.benefits_program_policy_id.name + " [" + self.name + "]"
        generic_dict = {
            'name': name,
            'company_id': self.company_id and self.company_id.id or False,
            'currency_id': self.currency_id and self.currency_id.id or False,
            'product_id': self.product_id and self.product_id.id or False,
            'date_maturity': self._get_current_date(),
            'journal_id': self.journal_id and self.journal_id.id or False,
            'date': self.accounting_date,
            'partner_id': self.employee_id.user_id.partner_id.id if
            self.employee_id.user_id and self.employee_id.user_id.partner_id
            else False,
            'quantity': 1,
            'move_id': move.id,
        }
        debit_entry_dict = {
            'account_id': self.debit_account_id.id,
            'debit': self.total_benefit,
            'analytic_account_id': self.account_analytic_id and
                                   self.account_analytic_id.id or False
        }
        credit_entry_dict = {
            'account_id': self.credit_account_id.id,
            'credit': self.total_benefit,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst

    @api.multi
    def action_move_create(self):
        # force the name to the default value, to avoid an eventual
        # 'default_name' in the context to set it to '' which cause no
        # number to be given to the account.move when posted.
        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id if self.journal_id else False,
            'company_id': self.company_id.id if self.company_id else False,
            'date': self.accounting_date,
            'ref': self.name,
            'name': '/',
        })
        if move:
            move_line_lst = self._prepare_move_lines(move)
            move.line_ids = move_line_lst
            self.write({'account_move_id': move.id})

    @api.multi
    def action_generate_journal_entry(self):
        """
        return Benefits Program reject
        :return:
        """
        for service in self:
            self._check_benefits_program_restrictions()
            if service.account_move_id:
                raise Warning(_('Already, The disbursement journal entry has '
                                'been created.'))
            service.action_move_create()
        return True

    @api.multi
    def action_open_journal_entries(self):
        """
        open journal entry
        :param self:
        :return:
        """
        res = self.env['ir.actions.act_window'].for_xml_id(
            'account', 'action_move_journal_line')
        res['domain'] = [('ref', 'in', self.mapped('name'))]
        res['context'] = {}
        return res

    # # Emails Related Methods
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
            'org_benefits_program.action_bp_request_for_view_all'
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
            'model': 'org.benefits.program'
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
            temp_xml_id = 'org_benefits_program.bp_request_send_to_manager'
        elif dest_state == 'vp_approval':
            temp_xml_id = 'org_benefits_program.bp_request_send_to_vp'
        elif dest_state == 'hr_approval':
            temp_xml_id = 'org_benefits_program.bp_request_send_to_hr_approval'
        elif dest_state == 'ceo_approval':
            temp_xml_id = 'org_benefits_program.bp_request_send_to_ceo'
        elif dest_state == 'finance_processing':
            temp_xml_id = 'org_benefits_program.' \
                          'bp_request_send_to_final_finance_processing'
        elif dest_state == 'approved':
            temp_xml_id = 'org_benefits_program.bp_request_approved'
        elif dest_state == 'return_to_draft':
            temp_xml_id = 'org_benefits_program.bp_request_return'
        elif dest_state == 'rejected':
            temp_xml_id = 'org_benefits_program.bp_request_rejected'
        elif dest_state == 'locked':
            temp_xml_id = 'org_benefits_program.bp_request_locked'
        elif dest_state == 'unlocked':
            temp_xml_id = 'org_benefits_program.bp_request_unlocked'

        if temp_xml_id:
            self._send_email(temp_xml_id, email_to)
        return True
