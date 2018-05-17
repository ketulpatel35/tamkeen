from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT

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
                  ('finance_processing', 'Finance Processing'),
                  ('waiting_repayment', 'Waiting Re-Payment'),
                  ('approved', 'Confirm'),
                  ('rejected', 'Rejected'),
                  ('closed', 'Closed'),
                  ('cancelled', 'Cancelled'),
                  ('locked', 'Locked')]


class EmployeeLoan(models.Model):
    _name = 'hr.employee.loan'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Employee Loan'
    _order = 'name desc'

    @api.model
    def _get_sequence(self):
        seq = self.env['ir.sequence'].next_by_code('hr.employee.loan')
        return seq

    @api.multi
    def unlink(self):
        for loan_rec in self:
            if loan_rec.state not in ['draft']:
                raise Warning("Only requests in draft state can be removed.")
            # remove related installment as well
            loan_rec.loan_installment_ids.unlink()
        return super(EmployeeLoan, self).unlink()

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self._get_sequence()
            res = super(EmployeeLoan, self).create(vals)
            if res.loan_approval_policy_id and not \
                    res.loan_approval_policy_id.allow_multiple_active_loans:
                loan_rec = self.search(
                    [('employee_id', '=', res.employee_id.id),
                     ('id', '!=', res.id), ('state','not in', ('closed',
                                                               'rejected',
                                                               'cancelled'))])
                if loan_rec:
                    raise Warning(_('Already, You have an active loan. '
                                    'For more information, Kindly '
                                    'check with the HR Team. '))
            # if res.loan_installment_policy == 'deserved':
            #     amount, installment_month = self. \
            #         _check_salary_rule(res.employee_id,
            #                            res.loan_approval_policy_id)
            #     res.loan_amount = amount
            #     res.installment_number = installment_month
            # res.repayment_method = res.loan_approval_policy_id.repayment_method
        return res

    @api.multi
    def copy(self, default=None):
        if not self._check_group(
                'employee_loan.group_loan_on_behalf_approval_srvs'):
            for rec in self:
                if rec.employee_id.user_id.id != self._uid:
                    raise Warning(_(
                        "You don't have the permissions to make such changes."
                    ))
        if self.loan_approval_policy_id:
            if self.loan_approval_policy_id.states_to_display_ids:
                stage_id = False
                for stage_rec in \
                        self.loan_approval_policy_id.states_to_display_ids:
                    if stage_rec.case_default:
                        stage_id = stage_rec.id
                        break
                if not self.stage_id:
                    stage_id = \
                        self.loan_approval_policy_id.states_to_display_ids[0].id
                default.update({'stage_id': stage_id})
        return super(EmployeeLoan, self).copy(default=default)

    @api.onchange('loan_installment_policy', 'employee_id')
    def onchange_loan_installment_policy(self):
        if self.loan_installment_policy:
            self.loan_installment_ids = False
            self.length_of_service_days = self.employee_id.length_of_service_days
            if self.loan_installment_policy == 'desired':
                self.loan_amount = 0
                self.installment_number = 0
            else:
                self.loan_installment_ids = False
                amount, installment_month = \
                    self._check_salary_rule(self.employee_id,
                                            self.loan_approval_policy_id)
                self.loan_amount = amount
                self.installment_number = installment_month

    def _get_service_month(self, employee):
        # We check the employee service days
        if employee and employee.initial_employment_date:
            srvc_months, dHire = \
                employee.get_months_service_to_date()[
                    employee.id]
        else:
            raise Warning(_('You should have a hiring date in your '
                            'profile.'))
        return srvc_months, dHire

    @api.multi
    def write(self, vals):
        for rec in self:
            if rec.state == 'draft':
                if rec.loan_approval_policy_id and not \
                        rec.loan_approval_policy_id.allow_multiple_active_loans:
                    loan_rec = self.search(
                        [('employee_id', '=', rec.employee_id.id),
                         ('id', '!=', rec.id), ('state','not in', ('closed',
                                                               'rejected',
                                                               'cancelled'))])
                    if loan_rec:
                        raise Warning(_('Already, You have an active loan. '
                                        'For more information, Kindly '
                                        'check with the HR Team.'))
        res = super(EmployeeLoan, self).write(vals)
        return res

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

    def _check_salary_rule(self, employee_rec, loan_approval_policy_id):
        srvc_months, dHire = self._get_service_month(employee_rec)
        convert_year = int(srvc_months) / 12
        installment_months = 0.0
        if loan_approval_policy_id and \
                loan_approval_policy_id.service_policy_ids:
            loan_policy_rec = loan_approval_policy_id.service_policy_ids \
                .search([(
                'company_experience_from', '<=', convert_year), (
                'company_experience_to', '>', convert_year),
                ('service_id', '=', loan_approval_policy_id.id)], limit=1)
            localdict = self._get_amount_localdict(employee_rec)
            if loan_policy_rec:
                deserved_amount = loan_policy_rec.deserved_amount
                amount_tuple = loan_policy_rec.deserved_amount_salary_rule_id \
                    .compute_rule(localdict)
                amount = amount_tuple[
                             0] * deserved_amount if amount_tuple else 0.0
                installment_months += loan_policy_rec.loan_deduction_period
            else:
                raise Warning(_('There are no matching policy based on your '
                                'years of experiece at the company,'
                                'Kindly, Check with HR Team.'))
        else:
            raise Warning(_('Kindly, Contact the HR Team to configure your '
                            'policy.'))
        return amount, installment_months

    @api.depends('loan_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.loan_approval_policy_id.sla_period or False
            sla_period_unit = \
                rec.loan_approval_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.loan_submit_date:
                    loan_submit_date = datetime.strptime(rec.loan_submit_date,
                                                         OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        loan_submit_date + _intervalTypes[
                            sla_period_unit](
                            sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    def _check_minimum_amount_loan(self):
        minimum_loan_amount = self.loan_approval_policy_id.minimum_loan_amount
        if self.loan_amount < minimum_loan_amount:
            raise Warning(_('Minimum loan amount to request: %s. ')
                          %minimum_loan_amount)
        return True

    @api.multi
    def calculate_loan_amount(self):
        if not self.loan_approval_policy_id:
            raise Warning(_('Kindly, Select a loan type.'))
        if not self.installment_number:
            raise Warning(_('Kindly, enter an installment count for '
                            'calculating installments.'))
        for rec in self:
            if rec.loan_installment_policy == 'desired':
                rec.check_for_loan_amount(
                    rec.employee_id, rec.loan_approval_policy_id,
                    rec.loan_amount, rec.installment_number)
            rec._check_minimum_amount_loan()
            rec.loan_installment_ids.unlink()
            if rec.loan_installment_policy == 'deserved':
                amount, installment_month = rec._check_salary_rule(
                        rec.employee_id, rec.loan_approval_policy_id)
                rec.write({'loan_amount': amount, 'installment_number':
                    installment_month, 'length_of_service_days':
                    rec.employee_id.length_of_service_days})
            payroll_run_day = rec.loan_approval_policy_id.payroll_run_day
            loan_installment_obj = self.env['loan.installments']
            loan_amount = rec.loan_amount
            installment_number = rec.installment_number
            if loan_amount and installment_number:
                amount = loan_amount / installment_number
                dtoday = date.today()
                payroll_run_date = dtoday + relativedelta(day=payroll_run_day)
                # create installment
                total_amount = 0.00
                du_date = 0
                for duration in range(1, installment_number):
                    loan_installment_obj.create({
                        'due_date': payroll_run_date + relativedelta(
                            months=duration),
                        'amount': round(amount, 2),
                        'state': 'draft',
                        'loan_id': rec.id
                    })
                    total_amount += round(amount, 2)
                    du_date = duration
                # last installment separate (for solve rounding issues)
                last_amount = loan_amount - total_amount
                loan_installment_obj.create({
                    'due_date': payroll_run_date + relativedelta(
                        months=du_date+1),
                    'amount': round(last_amount, 2),
                    'state': 'draft',
                    'loan_id': rec.id
                })

    @api.multi
    def clear_installment_line(self):
        for rec in self:
            for line in rec.loan_installment_ids:
                if line.state == 'draft':
                    line.unlink()

    @api.multi
    def _get_employee_name(self):
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.depends('loan_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.loan_submit_date:
                loan_submit_date = datetime.strptime(rec.loan_submit_date,
                                                     OE_DTFORMAT)
                if rec.loan_final_approval_date:
                    loan_final_approval_date = datetime.strptime(
                        rec.loan_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(loan_final_approval_date,
                                         loan_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, loan_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.loan_waiting_time = waiting_time

    @api.depends('loan_installment_ids')
    def compute_installment_payment(self):
        """
        compute
        - total paid installment amount
        - remaining installments total_amount
        :return:
        """
        for rec in self:
            total_paid_installment = 0.00
            for inst_line in rec.loan_installment_ids:
                if inst_line.state == 'done':
                    total_paid_installment += inst_line.amount
            rec.total_paid_installment_amount = total_paid_installment
            rec.remaining_installments_total_amount = \
                rec.loan_amount - total_paid_installment

    name = fields. \
        Char(string="Request Number", readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee Name',
                                  default=_get_employee_name,
                                  copy=False)
    employee_company_id = fields.Char(related='employee_id.f_employee_no',
                                      string='Employee Company ID',
                                      readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Organization Unit')
    length_of_service_days = fields.Integer(string='Length of Service by Days')
    cost_center_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")
    loan_approval_policy_id = fields.Many2one('service.configuration.panel',
                                              string='Loan Type')
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company',
                                 )
    about_loan_type = fields.Text(
        related='loan_approval_policy_id.about_service', string='About the '
                                                                'Service')
    loan_installment_policy = fields.Selection([
        ('deserved', 'Deserved'),
        ('desired', 'Desired')], string='Installment Policy')
    loan_amount = fields.Float('Loan Amount', readonly=True)
    installment_number = fields.Integer('Installments Count', readonly=True)

    remarks = fields.Char('Remarks')
    stage_id = fields.Many2one(
        'service.panel.displayed.states',
        string='States To Be Displayed',
        index=True,
        domain="[('service_type_ids', '=', loan_approval_policy_id)]",
        copy=False)
    state = fields.Selection(SERVICE_STATUS,
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             help='When the Loan is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded based on the service type '
                                  'configuration.',
                             default='draft')
    endorsement_loan_required = fields.Boolean(string='Endorsement Required',
                                               invisible=True)
    endorsement_loan_text = fields.Text(
        related='loan_approval_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_loan_approved = fields.Boolean(string='Endorsement Approved',
                                               track_visibility='onchange',
                                               readonly=1, copy=False,
                                               states={'draft': [('readonly',
                                                                  False)]})
    loan_submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
        help='It will be automatically filled by the user who requested the '
             'service.')
    loan_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                       copy=False)
    loan_waiting_time = fields.Char(compute=_calculate_ongoing_waiting_time,
                                    string='Waiting Time',
                                    method=True, copy=False,
                                    states={'draft': [('readonly', False)]})
    loan_final_approval_date = fields.Datetime('Final Approval Date',
                                               readonly=True, copy=False)
    loan_final_approval_user_id = fields.Many2one('res.users',
                                                  string='Final Approval',
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
    loan_return_user_id = fields.Many2one('res.users', string='Return By',
                                          readonly=True, copy=False)
    loan_return_date = fields.Datetime(string='Return Date',
                                       readonly=True, copy=False)
    loan_mngr_user_id = fields.Many2one('res.users', string='Manager Approval',
                                        readonly=True, copy=False)
    loan_mngr_approval_date = fields.Datetime(string='Manager Approval Date',
                                              readonly=True, copy=False)
    loan_vp_user_id = fields.Many2one('res.users', string='VP Approval',
                                      readonly=True, copy=False)
    loan_vp_approval_date = fields.Datetime(string='VP Approval Date',
                                            readonly=True, copy=False)
    loan_budget_user_id = fields.Many2one('res.users', string='Budget '
                                                              'Approval',
                                          readonly=True, copy=False)
    loan_budget_approval_date = fields.Datetime(string='Budget Approval Date',
                                                readonly=True, copy=False)
    loan_hr_user_id = fields.Many2one('res.users', string='HR Approval',
                                      readonly=True, copy=False)
    loan_hr_approval_date = fields.Datetime(string='HR Approval Date',
                                            readonly=True, copy=False,
                                            track_visibility='onchange')
    loan_service_log_ids = fields.One2many('service.log',
                                           'loan_request_id',
                                           string='Service Logs')
    loan_rejected_user_id = fields.Many2one('res.users', string='Rejected By',
                                            readonly=True, copy=False)
    loan_rejected_date = fields.Datetime(string='Rejected Date',
                                         readonly=True, copy=False)
    loan_locked_user_id = fields.Many2one('res.users', string='Locked By',
                                          readonly=True, copy=False)
    loan_locked_date = fields.Datetime(string='Locked Date',
                                       readonly=True, copy=False)
    locked_by = fields.Selection([('hr', 'HR'), ('finance', 'Finance'),
                                  ('budget', 'Budget')],
                                 string='Locked Team')
    loan_cancel_user_id = fields.Many2one('res.users', string='Cancel By',
                                          readonly=True, copy=False)
    loan_cancel_date = fields.Datetime(string='Cancel Date',
                                       readonly=True, copy=False)
    loan_proof_ids = fields.One2many('loan.proof', 'loan_id',
                                     string='Loan Proofs')
    # interest_mode = fields.Selection([
    #     ('flat', 'Flat'),
    #     ('reducing', 'Reducing')], string='Interest Mode')
    # loan_duration = fields.Integer('Loan Duration(Months)')
    # loan_rate = fields.Float('Rate')
    loan_installment_ids = fields.One2many('loan.installments', 'loan_id')
    repayment_method = fields.Selection([('payroll', 'Payroll'),
                                         ('cash_bank', 'Cash/Bank')],
                                        copy=False,
                                        string='RePayment Method')
    total_paid_installment_amount = fields.Float(
        compute='compute_installment_payment',
        string='Total Paid Installment Amount')
    remaining_installments_total_amount = fields.Float(
        compute='compute_installment_payment',
        string='Remaining Installments Total Amount')
    employee_performance_evaluation = fields.Float(
        string='Employee Performance Evaluation',
        copy=False, track_visibility='onchange')
    proof_required = fields.Boolean(
        related='loan_approval_policy_id.proof_required',
        string='Proof Required', store=True)
    arrival_time_to_finance = fields.Datetime('Arrival Time to Finance',
                                              copy=False)
    arrival_time_to_hr = fields.Datetime('Arrival Time to HR',
                                              copy=False)
    accounting_date = fields.Date(string='Accounting Date', copy=False)
    loan_journal_id = fields.Many2one('account.journal', string='Journal',
                                      copy=False)
    debit_account_id = fields.Many2one('account.account',
                                       string='Debit Account', copy=False)
    credit_account_id = fields.Many2one('account.account',
                                        string='Credit Account', copy=False)
    loan_issuing_date = fields.Date(string='Loan Issuing Date',
                                    default=_get_current_date, copy=False)
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
                                      copy=False)
    paid_to_employee = fields.Boolean(string='Paid to Employee', copy=False)
    submit_message = fields.Text(
        related='loan_approval_policy_id.submit_message',
        string='Submit Hint Message', store=True)

    def _get_loan_policy_id(self):
        if self.company_id and self.company_id.loan_policy_id:
            if self.company_id.loan_policy_id.valid_from_date and \
                    self.company_id.loan_policy_id.valid_to_date:
                today_date = datetime.today().date()
                from_date = datetime.strptime(
                    self.company_id.loan_policy_id.valid_from_date,
                    OE_DATEFORMAT).date()
                to_date = datetime.strptime(
                    self.company_id.loan_policy_id.valid_to_date,
                    OE_DATEFORMAT).date()
                if from_date <= today_date <= to_date:
                    return self.company_id.loan_policy_id
                else:
                    Warning(_('There is no an active policy for the loan'
                                ', For more information, Kindly '
                                'contact the HR Team.'))
            else:
                raise Warning(_('There is no an active policy for the loan'
                                ', For more information, Kindly '
                                'contact the HR Team.'))

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = False
        window_action_ref = \
            'employee_loan.hr_employee_loan_action'
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
            'model': 'hr.employee.loan'
        })
        return context

    @api.multi
    def _get_loan_related_stage_id(self, service, dest_state):
        stage_id = False
        states_to_display_pool = self.env['service.panel.displayed.states']
        stage_ids = states_to_display_pool.search([
            ('wkf_state', '=', str(dest_state)),
            ('model_id.model', '=', 'hr.employee.loan')])
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

    def _update_arrival_hr(self):
        self.write({'arrival_time_to_hr': self._get_current_datetime()})

    @api.multi
    def check_dest_state_send_email(self, dest_state):
        context = dict(self._context)
        if dest_state == 'vp_approval':
            self._send_email(
                'employee_loan.loan_pre_req_send_to_vp',
                None, dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'mngr_approval':
            self._send_email(
                'employee_loan.loan_request_send_manager',
                None, dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'budget_approval':
            self._send_email(
                'employee_loan.loan_pre_req_send_to_budget',
                None, dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'hr_approval':
            self._send_email(
                'employee_loan.loan_pre_req_send_to_hr', None,
                dest_state, self.id, 'hr_employee_loan')
            self._update_arrival_hr()
        elif dest_state == 'ceo_approval':
            self._send_email(
                'employee_loan.loan_req_send_to_ceo', None,
                dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'approved':
            self._send_email(
                'employee_loan.loan_req_approved', None,
                dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'rejected':
            self.reject_loan_installment()
            self.with_context(context)._send_email(
                'employee_loan.email_template_loan_request_reject', None,
                dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'draft':
            self._send_email(
                'employee_loan.email_template_loan_draft', None,
                dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'waiting_repayment':
            self.write({'paid_to_employee': True})
            self.confirm_loan_installment()
            self._send_email('employee_loan.loan_amount_paid_to_employee',
                             None, dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'closed':
            self.closed_loan_installment()
            self._send_email('employee_loan.loan_req_closed', None,
                             dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'locked':
            self._send_email('employee_loan.loan_req_locked_to_employee', None,
                             dest_state, self.id, 'hr_employee_loan')
        elif dest_state == 'finance_processing':
            self._send_email('employee_loan.loan_pre_req_send_to_finance',
                             None, dest_state, self.id, 'hr_employee_loan')
        return True

    @api.multi
    def _get_loan_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
        # service_states.append('refused') # to add the refused state
        service_states.append('finance_processing')  # to add the
        service_states.append('waiting_repayment')
        service_states.append('approved')
        # approved state'
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    def _get_loan_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_loan_related_stage_id(service, dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for  "
                "%s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'loan_submitted_by': self.env.user.id,
                           'loan_submit_date': self._get_current_datetime()})
        if current_state == 'mngr_approval':
            result.update(
                {'state': dest_state, 'loan_mngr_user_id': self.env.user.id,
                 'loan_mngr_approval_date': self._get_current_datetime()})
        if current_state == 'vp_approval':
            result.update(
                {'state': dest_state, 'loan_vp_user_id': self.env.user.id,
                 'loan_vp_approval_date': self._get_current_datetime()})
        if current_state == 'budget_approval':
            result.update(
                {'state': dest_state, 'loan_budget_user_id': self.env.user.id,
                 'loan_budget_approval_date': self._get_current_datetime()})
        if current_state == 'hr_approval':
            result.update(
                {'state': dest_state, 'loan_hr_user_id': self.env.user.id,
                 'loan_hr_approval_date': self._get_current_datetime()})
        if current_state == 'ceo_approval':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        if current_state == 'finance_processing':
            result.update(
                {'state': dest_state})
        if current_state == 'open':
            result.update(
                {'state': dest_state})
        if current_state == 'rejected':
            result.update(
                {'state': dest_state})
        if current_state == 'locked':
            result.update(
                {'state': dest_state})
        if current_state == 'waiting_repayment':
            result.update(
                {'state': dest_state})
        return result

    @api.onchange('company_id')
    def onchange_company_id(self):
        pre_request_id = self._get_loan_policy_id()
        if not pre_request_id:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the loan policy has been '
                            'applied.'))
        if not self.loan_approval_policy_id:
            self.loan_approval_policy_id = pre_request_id.id
        if self.loan_approval_policy_id:
            self.onchange_loan_policy()

    @api.onchange('loan_approval_policy_id')
    def onchange_loan_policy(self):
        if self.loan_approval_policy_id:
            self.endorsement_loan_required = \
                self.loan_approval_policy_id.endorsement_required
            self.loan_installment_policy = self. \
                loan_approval_policy_id.loan_installment_policy
            self.repayment_method = self. \
                loan_approval_policy_id.repayment_method
            # proof required
            proof_lst = []
            if self.proof_required:
                self.loan_proof_ids.unlink()
                for line in self.loan_approval_policy_id.service_proof_ids:
                    proof_lst.append((0, 0, {'name': line.name, 'description':
                        line.description, 'mandatory': line.mandatory}))
            self.loan_proof_ids = proof_lst
            if self.loan_approval_policy_id.states_to_display_ids:
                for stage_rec in \
                        self.loan_approval_policy_id.states_to_display_ids:
                    if stage_rec.case_default:
                        self.stage_id = stage_rec.id
                        break
                    if not self.stage_id:
                        self.stage_id = \
                            self.loan_approval_policy_id.states_to_display_ids[
                            0].id
            self.onchange_loan_installment_policy()

    @api.model
    def check_for_loan_amount(self, employee_rec, loan_approval_policy_id,
                              loan_amount, installment_months):
        if loan_amount or installment_months:
            amount, month = self._check_salary_rule(employee_rec,
                                                    loan_approval_policy_id)
            if round(loan_amount, 2) > round(amount,2) or \
                            int(installment_months) > int(month):
                raise Warning(_('As per the company policy you are eligible '
                                'only for %s and you should repay them within '
                                '%s month/s only.') % (round(amount, 2), month))

    def _check_employee_length_service(self, employee_rec):
        if int(self.length_of_service_days) < \
                int(employee_rec.length_of_service_days):
            raise Warning(_('Kindly, Calculate your loan installments again '
                            'since your length of service by days more than '
                            'the previous calculation days.'))
        return True


    @api.multi
    def action_submit_for_loan_approval(self):
        """
        method call from Button Submit for Approval
        :return:
        """
        # check condition
        # self.check_proofs()
        for rec in self:
            if not rec.loan_approval_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the loan policy has been applied.'))
            rec.check_for_loan_amount(
                rec.employee_id, rec.loan_approval_policy_id,
                self.loan_amount, self.installment_number)
            rec._check_employee_length_service(rec.employee_id)
        allow_behalf_req = self._check_group(
            'employee_loan.group_loan_on_behalf_approval_srvs')
        if not allow_behalf_req:
            employee_rec = self.env['hr.employee'] \
                .search([('user_id', '=', self._uid)], limit=1)
            if self.employee_id != employee_rec:
                raise Warning(_('You are not allowed to do this change on '
                                'behalf of others.'))
        if not rec.loan_installment_ids:
            raise Warning(_('Kindly, click on calculate button to have a '
                            'full picture on your amortization schedule.'))
        self._check_point_for_all_stage()

        # All Button Comman method

    @api.multi
    def _check_point_for_all_stage(self):
        """
        All button have t_get_loan_policy_ido check and run this code
        :return:
        """
        if self.is_transition_allowed('mngr_approval'):
            self.service_loan_submit_mngr()
        elif self.is_transition_allowed('vp_approval'):
            self.loan_service_validate1()
        elif self.is_transition_allowed('budget_approval'):
            self.loan_service_validate2()
        elif self.is_transition_allowed('hr_approval'):
            self.loan_service_validate3()
        elif self.is_transition_allowed('ceo_approval'):
            self.loan_service_validate4()
        else:
            return False
        return True

    @api.multi
    def service_loan_submit_mngr(self):
        for service in self:
            dest_state = self._get_loan_dest_state(service)
            self._check_loan_service_restrictions()
            if dest_state:
                self.write(
                    self._get_loan_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
                # self._send_email('hr_overtime.overtime_pre_req_send_manager')
                return True

    @api.multi
    def _check_user_permissions(self, signal='approve'):
        for rec in self:
            if not rec._check_group(
                    'employee_loan.group_loan_self_approval_srvs'):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(_("Please, Make sure that you have"
                                    " the rights to %s your own request.")
                                  % (signal))
        return False

    @api.multi
    def loan_service_validate1(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = self._get_loan_dest_state(service)
            if dest_state:
                self.write(
                    self._get_loan_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def loan_service_validate2(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = self._get_loan_dest_state(service)
            if dest_state:
                self.write(
                    self._get_loan_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def loan_service_validate3(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = self._get_loan_dest_state(service)
            if dest_state:
                self.write(
                    self._get_loan_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def loan_service_validate4(self):
        for service in self:
            self._check_user_permissions('approve')
            # check validation for hr approval
            if not service.employee_performance_evaluation and \
                    self.loan_approval_policy_id.performance_evaluation_required:
                raise Warning(_('To proceed, Kindly add the performance '
                                'evaluation value for this employee.'))
            self._check_loan_service_restrictions()
            dest_state = self._get_loan_dest_state(service)
            if dest_state == 'finance_processing':
                final_approval = {
                    'loan_final_approval_user_id': self.env.user.id,
                    'loan_final_approval_date': self._get_current_datetime(),
                    'open_user_id': self.env.user.id,
                    'open_date': self._get_current_datetime(),
                    'arrival_time_to_finance': self._get_current_datetime(),
                }
                self.write(final_approval)
            if dest_state:
                self.write(
                    self._get_loan_approval_info(service, dest_state))
                self.check_dest_state_send_email(dest_state)
            return True

    @api.multi
    def loan_service_validate5(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = self._get_loan_dest_state(service)
            final_approval = {
                'loan_final_approval_user_id': self.env.user.id,
                'loan_final_approval_date': self._get_current_datetime(),
                'open_user_id': self.env.user.id,
                'open_date': self._get_current_datetime(),
                'arrival_time_to_finance': self._get_current_datetime(),
            }
            self.write(final_approval)
            self.write(
                self._get_loan_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def service_validate8(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = 'closed'
            self.write({'closed_user_id': self.env.user.id, 'closed_date':
                self._get_current_datetime()})
            self.write(
                self._get_loan_approval_info(service,
                                             dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def check_installment_done(self):
        """
        check all installment is in done state then Lone record also in done
        state.
        :return:
        """
        for loan_rec in self:
            flag = [True for inst_rec in loan_rec.loan_installment_ids if \
                    inst_rec.state != 'done']
            if not flag:
                loan_rec.service_validate8()

    @api.multi
    def loc_service_validate10(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = 'draft'
            service.write({
                'loan_submit_date': False,
                'loan_submitted_by': False,
                'loan_mngr_user_id': False,
                'loan_mngr_approval_date': False,
                'loan_vp_user_id': False,
                'loan_vp_approval_date': False,
                'loan_hr_user_id': False,
                'loan_hr_approval_date': False,
                'loan_budget_user_id': False,
                'loan_budget_approval_date': False,
                'loan_ceo_user_id': False,
                'loan_ceo_approval_date': False,
                'loan_closed_user_id': False,
                'loan_closed_date': False,
                'loan_rejected_user_id': False,
                'loan_rejected_date': False,
                'loan_locked_user_id': False,
                'loan_locked_date': False,
                'loan_cancel_user_id': False,
                'loan_cancel_date': False,
                'expected_approval_date_as_sla': False,
                'loan_final_approval_date': False,
                'loan_final_approval_user_id': False,
                'loan_waiting_time': False,
                'arrival_time_to_finance': False,
            })
            service.loan_hr_approval_date = False
            service.loan_hr_user_id = False
            self.write({'loan_return_user_id': self.env.user.id,
                        'loan_return_date':
                            self._get_current_datetime()})
            self.write(
                self._get_loan_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def confirm_loan_installment(self):
        for rec in self:
            for line in rec.loan_installment_ids:
                line.write({'state': 'payroll_processing'})

    @api.multi
    def cancel_loan_installment(self):
        for rec in self:
            for line in rec.loan_installment_ids:
                line.write({'state': 'cancel'})

    @api.multi
    def reject_loan_installment(self):
        for rec in self:
            for line in rec.loan_installment_ids:
                line.write({'state': 'reject'})

    @api.multi
    def closed_loan_installment(self):
        for rec in self:
            for line in rec.loan_installment_ids:
                line.write({'state': 'done'})

    def _prepare_move_lines(self, move):
        move_lst = []
        generic_dict = {
            'name': self.name,
            'company_id': self.env.user.company_id.id if
            self.env.user.company_id else False,
            'currency_id': self.env.user.company_id.currency_id.id if
            self.env.user.company_id and
            self.env.user.company_id.currency_id else False,
            'date_maturity': self.loan_issuing_date,
            'journal_id': self.loan_journal_id.id if self.loan_journal_id
            else False,
            'date': self.accounting_date,
            'partner_id': self.employee_id.user_id.partner_id.id if
            self.employee_id.user_id and self.employee_id.user_id.partner_id
            else False,
            'quantity': 1,
            'move_id': move.id,
        }
        debit_entry_dict = {
            'account_id': self.credit_account_id.id,
            'debit': self.loan_amount,
        }
        credit_entry_dict = {
            'account_id': self.debit_account_id.id,
            'credit': self.loan_amount,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst

    @api.multi
    def action_move_create(self):
        move = self.env['account.move'].create({
            'journal_id': self.loan_journal_id.id if self.loan_journal_id
            else False,
            'company_id': self.env.user.company_id.id if
            self.env.user.company_id else False,
            'date': self.accounting_date,
            'ref': self.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        })
        if move:
            move_line_lst = self._prepare_move_lines(move)
            move.line_ids = move_line_lst
            self.write({'account_move_id': move.id})

    @api.multi
    def button_finance_processing(self):
        for loan in self:
            if loan.account_move_id:
                raise Warning(_('Already, The disbursement journal entry has '
                                'been '
                                'created.'))
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            # dest_state = 'approved'
            # dest_state = self._get_loan_dest_state(service)
            # self.write(
            #     self._get_loan_approval_info(service, dest_state))
            loan.action_move_create()
            # self.check_dest_state_send_email(dest_state)
        return True

    @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].for_xml_id('account',
                                                           'action_move_journal_line')
        # DO NOT FORWARD-PORT
        res['domain'] = [('ref', 'in', self.mapped('name'))]
        res['context'] = {}
        return res

    @api.multi
    def update_installments(self, reschedule_date):
        for rec in self:
            sorting_installment_rec = rec.loan_installment_ids.sorted()
            payroll_run_day = self.loan_approval_policy_id.payroll_run_day
            start_date = datetime.strptime(reschedule_date, OE_DATEFORMAT) + \
                         relativedelta(
                day=payroll_run_day)
            for installment in sorting_installment_rec:
                start_date += relativedelta(months=1)
                installment.write({'due_date': start_date})
        return True

    @api.multi
    def button_confirm(self, reschedule_date, status):
        self._check_loan_service_restrictions()
        dest_state = self._get_loan_dest_state(self)
        self.write(
            self._get_loan_approval_info(self, dest_state))
        self.write({'loan_issuing_date': reschedule_date})
        self.check_dest_state_send_email(dest_state)
        if status == 'yes':
            self.update_installments(reschedule_date)

    @api.multi
    def button_paid_to_employee(self):
        for loan in self:
            if not loan.account_move_id:
                raise Warning(_('Kindly, Generate the journal entry first.'))
            update_issuing_date_view = self.env.ref(
                'employee_loan.reschedule_issuing_date_view', False)
            return {
                'name': _('Reschedule Issuing Date'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'reschedule.issuing.date',
                'views': [(update_issuing_date_view.id, 'form')],
                'view_id': update_issuing_date_view.id,
                'target': 'new',
            }
        return True

    @api.multi
    def loan_service_validate6(self):
        context = dict(self._context)
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = 'rejected'
            self.write({'loan_rejected_user_id': self.env.user.id,
                        'loan_rejected_date':
                            self._get_current_datetime()})
            self.write(
                self._get_loan_approval_info(service, dest_state))
            self.with_context(context).check_dest_state_send_email(
                dest_state)
        return True

    def loan_service_validate7(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = 'locked'
            self.write({
                'loan_locked_user_id': self.env.user.id,
                'loan_locked_date': self._get_current_datetime()})
            self.write(
                self._get_loan_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
            self.locked_by = self._context.get('locked_by')
        return True

    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    def loan_service_validate8(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_loan_service_restrictions()
            dest_state = ''
            if self.locked_by == 'hr':
                if not self._check_group(
                        'employee_loan.group_loan_hr_approval'):
                    raise Warning(
                        _('You are not allowed to unlock this request since '
                          'it has been locked by other teams.'))
                dest_state = 'hr_approval'
            elif self.locked_by == 'finance':
                if not self._check_group(
                        'employee_loan.group_loan_finance_approval'):
                    raise Warning(
                        _('You are not allowed to unlock this request since '
                          'it has been locked by other teams.'))
                dest_state = 'finance_processing'
            elif self.locked_by == 'budget':
                if not self._check_group(
                        'employee_loan.group_loan_budget_approval'):
                    raise Warning(
                        _('You are not allowed to unlock this request since '
                          'it has been locked by other teams.'))
                dest_state = 'budget_approval'
            # self.write({
            #     'loan_locked_user_id': self.env.user.id,
            #     'loan_locked_date': self._get_current_datetime()})
            self.write(
                self._get_loan_approval_info(service, dest_state))
            self.check_dest_state_send_email(dest_state)
            self.locked_by = self._context.get('locked_by')
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
    def _check_loan_service_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.loan_approval_policy_id.attachment_mandatory
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
            if service.loan_approval_policy_id.endorsement_required and not \
                    service.endorsement_loan_approved:
                raise Warning(
                    _("To proceed, Kindly agree on the endorsement."))

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.loan_approval_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.loan_approval_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.loan_approval_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.loan_approval_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.loan_approval_policy_id.ceo_approval:
                if service.employee_performance_evaluation < \
                        service.loan_approval_policy_id. \
                                employee_performance_evaluation:
                    req_approvals.append('ceo_approval')
        return req_approvals

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
        #     template_id = ir_model_data.get_object_reference(
        #         'hr_employee_state', 'email_template_termination_emp')[1]
        # except ValueError:
        #     template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        # ctx = dict(self.env.context or {})
        # ctx.update({
        #     'default_model': 'hr.employee.termination',
        #     'default_res_id': self.ids[0],
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'default_message_type': 'email',
        #     'mark_so_as_sent': True
        # })
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

    # Sending REMINDER Releted methods

    @api.one
    def _get_dest_email_to(self):
        email_to = None
        current_state = self.state
        if current_state == 'mngr_approval':
            email_to = self.employee_id.loan_manager_id.work_email
        elif current_state == 'vp_approval':
            email_to = self.employee_id.loan_vp_id.work_email
        elif current_state == 'hr_approval':
            email_to = self.loan_approval_policy_id.hr_email
        elif current_state == 'budget_approval':
            email_to = self.loan_approval_policy_id.budget_email
        elif current_state == 'ceo_approval':
            email_to = self.employee_id.loan_ceo_id.work_email
        elif current_state == 'finance_processing':
            email_to = self.loan_approval_policy_id.finance_email
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
            last_approval_date = self.loan_submit_date
        else:
            previous_state = req_approvals[current_state_index - 1]
            if previous_state == 'mngr_approval':
                last_approval_date = self.loan_mngr_approval_date
            elif previous_state == 'vp_approval':
                last_approval_date = self.loan_vp_approval_date
            elif previous_state == 'hr_approval':
                last_approval_date = self.loan_hr_approval_date
            elif previous_state == 'budget_approval':
                last_approval_date = self.loan_budget_approval_date
            elif previous_state == 'ceo_approval':
                last_approval_date = self.loan_ceo_approval_date
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
            ('state', 'not in', ['draft', 'rejected', 'closed', 'locked',
                                 'approved', 'cancelled', 'waiting_repayment']),
            ('loan_submit_date', '<',
             datetime.now().strftime('%Y-%m-%d 00:00:00'))
        ]
        loan_requested_recs = self.search(where_clause)
        for loan_req_rec in loan_requested_recs:
            req_approvals = loan_req_rec._get_service_req_approvals()
            if loan_req_rec.state in req_approvals:
                # It may happen in case of changing the required approvals
                # before finalizing the pending, so it will be skipped.
                approval_delay_diff = \
                    loan_req_rec._get_approval_delay(req_approvals)
                if loan_req_rec.loan_approval_policy_id.approval_reminder_line:
                    delay_to_remind = loan_req_rec.loan_approval_policy_id. \
                        approval_reminder_line.delay
                else:
                    # default take 1 day
                    delay_to_remind = 1
                if approval_delay_diff > \
                        delay_to_remind:
                    email_to = loan_req_rec._get_dest_email_to()
                    temp_id = 'employee_loan.' \
                              'loan_req_approval_reminder_cron_email_template'
                    loan_req_rec._send_email(temp_id, email_to,
                                             loan_req_rec.state,
                                             loan_req_rec.id,
                                             'hr_employee_loan')
        return True


class ResCompany(models.Model):
    _inherit = 'res.company'

    loan_policy_id = fields.Many2one('service.configuration.panel',
                                     string='Default Loan Policy')


class ServiceLog(models.Model):
    _inherit = 'service.log'

    loan_request_id = fields.Many2one('hr.employee.loan',
                                      string='Loan Request')
    installment_id = fields.Many2one('loan.installments',
                                     string='Loan Installment')
    loan_date_from = fields.Date('Date From')
    loan_date_to = fields.Date('Date TO')


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
            if str(context.get('active_model')) == 'hr.employee.loan':
                service_log_rec.write(
                    {'loan_request_id': active_rec.id})
            if str(context.get('active_model')) == 'hr.employee.loan':
                if context.get('trigger') and context.get(
                        'trigger') == 'Rejected':
                    active_rec.with_context({
                        'reason': self.reason}).loan_service_validate6()
                if context.get('trigger') and context.get(
                        'trigger') == 'Locked':
                    active_rec.loan_service_validate7()
                # if context.get('trigger') and context.get(
                #         'trigger') == 'Closed':
                #     active_rec.loan_service_validate8()
                # if context.get('trigger') and \
                #                 context.get('trigger') == 'Cancelled':
                #     active_rec.loan_service_validate9()
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.loc_service_validate10()
        return service_log_rec


class LoanInstallments(models.Model):
    _name = 'loan.installments'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee',
                                  related='loan_id.employee_id',
                                  string='Employee', store=True)
    due_date = fields.Date(string='Due Date')
    amount = fields.Float('Amount')
    remarks = fields.Text(string='Remarks')
    loan_id = fields.Many2one('hr.employee.loan', string='Loan Request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('payroll_processing', 'Payroll Processing'), ('amendment_created',
                                                       'Amendment Created'),
        ('finance_processing', 'Finance Processing'),
        ('ask_for_reschedule', 'Asked for Rescheduling'),
        ('reject', 'Reject'),
        ('lock', 'Rescheduled'), ('done', 'Done')], string='State',
        default='draft')
    installments_service_log_ids = fields.One2many(
        'service.log', 'installment_id', string='Service Logs')
    amendment_id = fields.Many2one('hr.payslip.amendment', string='Payslip '
                                                                  'Amendment')
    payroll_period_id = fields.Many2one('hr.payroll.period',
                                        string='Payroll Period',
                                        related='amendment_id.pay_period_id',
                                        store=True)

    @api.multi
    def generate_pyaslip_amendment(self):
        for rec in self:
            rec._check_policy()
            amendment_wizard_form = self.env.ref(
                'employee_loan.loan_generate_payslip_amendment_view', False)
            return {
                'name': _('Generate Payslip Amendment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'loan.generate.payslip.amendment',
                'views': [(amendment_wizard_form.id, 'form')],
                'view_id': amendment_wizard_form.id,
                'target': 'new',
            }

    def add_stage_log(self, vals):
        # Add Stage log
        stage_log_obj = self.env['service.log']
        loan_date_from = self.due_date
        state_to = self._context.get('trigger') or vals.get('state')
        stage_log_obj.create({'installment_id': self.id,
                              'state_from': self.state,
                              'state_to': state_to,
                              'loan_date_from': loan_date_from,
                              # 'loan_date_to': loan_date_to,
                              'user_id': self._uid})

    @api.multi
    def write(self, vals):
        if vals.get('state'):
            self.add_stage_log(vals)
        return super(LoanInstallments, self).write(vals)

    @api.multi
    def unlink(self):
        for loan_inst_rec in self:
            if loan_inst_rec.state not in ['draft']:
                raise Warning("Only requests in draft state can be removed.")
        return super(LoanInstallments, self).unlink()

    @api.multi
    def _check_group(self, group_xml_id):
        user_rec = self.env.user
        if user_rec.has_group(str(group_xml_id)):
            return True
        return False

    @api.multi
    def copy(self, default=None):
        if not self._check_group(
                'employee_loan.group_loan_on_behalf_approval_srvs'):
            for rec in self:
                if rec.employee_id.user_id.id != self._uid:
                    raise Warning(_("You don't have the permissions to make "
                                    "such changes."))
        return super(LoanInstallments, self).copy(default=default)

    @api.multi
    def _send_email(self, template_xml_ref, email_to, id):
        display_link = False
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url.static')
        if template_xml_ref:
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            template_id = data_pool.get_object_reference(
                'employee_loan', template_xml_ref)[1]
            action_id = self._get_related_window_action_id(data_pool)
            if action_id:
                display_link = True
            template_rec = template_pool.browse(template_id)
            if template_rec:
                ctx = {
                    'email_to': email_to,
                    'base_url': base_url,
                    'display_link': display_link,
                    'action_id': action_id,
                    'model': 'loan.installments'
                }
                if self._context and self._context.get('reason'):
                    ctx.update({'reason': self._context.get('reason')})
                template_rec.with_context(ctx).send_mail(id, force_send=False)
            return True

    @api.multi
    def ask_for_reschedule(self):
        for rec in self:
            # send mail
            self._send_email('loan_inst_ask_for_reschedule', False, rec.id)
            rec.write({'state': 'ask_for_reschedule'})

    @api.multi
    def button_reschedule(self):
        for rec in self:
            if rec.loan_id:
                last_installment_rec = self.search([('loan_id', '=',
                                                     rec.loan_id.id)],
                                                   order='due_date desc',
                                                   limit=1)
                due_date = datetime.strptime(last_installment_rec.due_date,
                                             OE_DATEFORMAT)
                rec.write({'due_date': due_date + relativedelta(months=1)})
            rec._send_email('loan_inst_reschedule', False, rec.id)
            rec.write({'state': 'payroll_processing'})

    @api.multi
    def button_reject_rescheduling(self):
        """
        reject from rescheduling
        :return:
        """
        for rec in self:
            rec._send_email('loan_inst_rescheduling_reject', False, rec.id)
            rec.write({'state': 'payroll_processing'})

    @api.multi
    def button_done(self):
        for rec in self:
            rec.write({'state': 'done'})

    def _check_policy(self):
        if self.loan_id and not self.loan_id.loan_approval_policy_id:
            raise Warning(_('There should be a predefined policy associated '
                            'with the company.'))

    @api.multi
    def get_payslip_amendment(self):
        context = dict(self._context)
        ids = []
        if context.get('active_ids'):
            ids = context.get('active_ids')
        else:
            ids = self.ids
        return {
            'name': 'Loan Payslip Amendments',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip.amendment',
            'target': 'current',
            'context': context,
            'domain': [('loan_installment_id', 'in', ids)]
        }

    @api.multi
    def _get_related_window_action_id(self, data_pool):
        window_action_id = False
        window_action_ref = \
            'employee_loan.loan_installments_action'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def send_reminder_loan_installment_ask_for_reschedule(self):
        """
        send reminder loan installment ask for reschedule
        :return:
        """
        loan_installment_rec = self.search([
            ('state', '=', 'ask_for_reschedule')])
        for loan_instal_rec in loan_installment_rec:
            if loan_instal_rec.loan_id.loan_approval_policy_id:
                email_to = loan_instal_rec.loan_id.loan_approval_policy_id. \
                    ask_for_reschedule_email
                self._send_email('loan_inst_ask_for_reschedule_reminder',
                                 email_to, loan_instal_rec.id)
        return True


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    is_loan = fields.Boolean('is Loan')

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        model_id = self.env['ir.model'].search([('model', '=',
                                                 'hr.employee.loan')])
        if self._context.get('loan_model'):
            res.update({
                'is_loan': True,
                'model_id': model_id.id or False})
        return res
