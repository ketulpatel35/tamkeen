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


class OrgBusinessTrip(models.Model):
    _name = 'org.business.trip'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Training & Business Trip'
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

    @api.multi
    def _get_employee_name(self):
        """
        :return:
        """
        employee_rec = self.env['hr.employee'].search([
            ('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    @api.depends('actual_start_date', 'actual_end_date')
    def _calculate_number_of_days(self):
        """
        calculate number of days in between two dates.
        :return:
        """
        for rec in self:
            if rec.actual_start_date and rec.actual_end_date:
                rec.number_of_days = self.get_diff_days(rec.actual_start_date,
                                                        rec.actual_end_date)
            else:
                rec.number_of_days = 0

    @api.depends('trip_departure_date', 'trip_return_date')
    def _calculate_request_of_days(self):
        """
        :return:
        """
        for rec in self:
            if rec.trip_departure_date and rec.trip_return_date:
                rec.total_request_days = self.get_diff_days(
                    rec.trip_departure_date, rec.trip_return_date)
            else:
                rec.total_request_days = 0

    @api.depends('bt_final_approval_date')
    def _calculate_ongoing_waiting_time(self):
        # res = dict.fromkeys(ids, 0)
        for rec in self:
            waiting_time = diff = ""
            now = datetime.strptime(self._get_current_datetime(), OE_DTFORMAT)
            if rec.bt_submit_date:
                bt_submit_date = datetime.strptime(
                    rec.bt_submit_date, OE_DTFORMAT)
                if rec.bt_final_approval_date:
                    bt_final_approval_date = datetime.strptime(
                        rec.bt_final_approval_date, OE_DTFORMAT)
                    diff = relativedelta(bt_final_approval_date,
                                         bt_submit_date)
                elif rec.state not in ['draft', 'refused', 'approved']:
                    diff = relativedelta(now, bt_submit_date)
            if diff:
                if diff.days:
                    waiting_time += str(diff.days) + " (D) "
                if diff.hours:
                    waiting_time += str(diff.hours) + " (H) "
                if diff.minutes:
                    waiting_time += str(diff.minutes) + " (M) "
                if diff.seconds:
                    waiting_time += str(diff.seconds) + " (S)"
            rec.bt_waiting_time = waiting_time

    @api.depends('bt_submit_date')
    def _calculate_expected_approval_date_as_sla(self):
        """
        :return:
        """
        for rec in self:
            expected_approval_date_as_sla = False
            # if rec.state not in ['draft','done','refused','approved']:
            sla_period = rec.business_trip_policy_id.sla_period or False
            sla_period_unit = \
                rec.business_trip_policy_id.sla_period_unit or False
            if sla_period and sla_period_unit:
                if rec.bt_submit_date:
                    bt_submit_date = datetime.strptime(
                        rec.bt_submit_date, OE_DTFORMAT)
                    expected_approval_date_as_sla = \
                        bt_submit_date + _intervalTypes[
                            sla_period_unit](sla_period)
            rec.expected_approval_date_as_sla = expected_approval_date_as_sla

    @api.depends('state_id', 'country_id')
    def _get_max_allowed_travel_days(self):
        """
        get maximum allow travel date
        :return:
        """
        for rec in self:
            if rec.business_trip_policy_id and rec.country_id:
                for bt_cal_rec in rec.business_trip_policy_id. \
                        business_trip_calculation_ids:
                    if bt_cal_rec.bt_countries_group_id:
                        if rec.country_id.id in bt_cal_rec. \
                                bt_countries_group_id.country_ids.ids:
                            rec.maximum_allowed_travel_days = \
                                bt_cal_rec.bt_countries_group_id. \
                                    maximum_allowed_travel_days
                            if self.company_id.country_id.id and \
                                            rec.country_id.id == \
                                            self.company_id.country_id.id \
                                    and not rec.business_trip_policy_id.\
                                            display_internal_city_only:
                                rec.maximum_allowed_travel_days += 1

    @api.depends('bt_allowance_cal_ids')
    def _calculate_total_amount(self):
        """
        Calculate total amount
        :return:
        """
        for rec in self:
            total = 0
            for cal_rec in rec.bt_allowance_cal_ids:
                total += cal_rec.amount
            rec.total_amount = total

    @api.depends('total_amount', 'total_training_cost', 'currency_id')
    def _calculate_total_estimation_cost(self):
        for rec in self:
            amount = rec.total_training_cost
            if rec.currency_id and rec.currency_id.id \
                                != self.env.user.company_id.currency_id.id:
                from_currency = rec.currency_id
                to_currency = self.env.user.company_id.currency_id
                amount = from_currency.compute(rec.total_training_cost,
                                               to_currency, round=True)
            total = rec.total_amount + amount
            rec.total_estimation_cost = total

    @api.depends('number_of_days', 'maximum_allowed_travel_days')
    def _calculate_total_trip_days(self):
        """
        Calculate total Trip Days
        :return:
        """
        for rec in self:
            rec.total_trip_days = rec.maximum_allowed_travel_days + \
                                  rec.number_of_days

    @api.multi
    def _count_service_request(self):
        """
        :return:
        """
        for rec in self:
            service_req_count = self.env['service.request'].search_count([
                ('reference_id','=', str(rec._name) + ',' + str(rec.id))])
            rec.service_request_count = service_req_count

    def search_service_request(self, operator, value):
        """
        :return:
        """
        rec_list = []
        for rec in self:
            service_req_count = self.env['service.request'].search_count([
                ('reference_id','=', str(rec._name) + ',' + str(rec.id))])
            if service_req_count:
                rec_list.append(rec.id)
        return [('id', 'in', rec_list)]

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
    actual_start_date = fields.Date('Actual Start Date', copy=False)
    actual_end_date = fields.Date('Actual End Date', copy=False)
    trip_departure_date = fields.Date('Trip Departure Date', copy=False)
    trip_return_date = fields.Date('Trip Return Date', copy=False)
    maximum_allowed_travel_days = fields.Integer(
        'Maximum Allowed Travel Days', compute='_get_max_allowed_travel_days',
        store=1)
    number_of_days = fields.Integer(
        'Number of Days', compute='_calculate_number_of_days', store=True)
    total_request_days = fields.Integer(
        'Total Trip Days', compute='_calculate_request_of_days', store=True)
    total_trip_days = fields.Integer(
        'Total Trip Days', compute='_calculate_total_trip_days', store=True)
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict')
    state_id = fields.Many2one(
        "res.country.state", string='City', ondelete='restrict')
    trip_purpose = fields.Selection([('training', 'Training'),
                                     ('business_trip', 'Business Trip'),
                                     ('conference', 'Conference'),
                                     ('event', 'Event'),
                                     ('other', 'Other')],
                                    string='Trip Purpose',
                                    default='business_trip')
    purpose_reason = fields.Char(string='Purpose Reason')
    training_description = fields.Text(string='Training Description')
    vendor_name = fields.Char(string='Vendor Name')
    total_training_cost = fields.Float(string='Total Training Cost')
    total_estimation_cost = fields.Float('Total Estimation Cost',
                                         compute='_calculate_total_estimation_cost', store=True)
    currency_id = fields. \
        Many2one('res.currency',
                 string='Currency',
                 default=lambda self:
                 self.env.user.company_id.currency_id.id,
                 required=True, readonly=True,
                 states={'draft': [('readonly', False)]})
    company_currency_id = fields. \
        Many2one('res.currency',
                 string='Currency',
                 default=lambda self:
                 self.env.user.company_id.currency_id.id)
    # is_invitation = fields.Selection(
    #     [('yes', 'Yes'), ('no', 'No')], default='no',
    #     string="Is your trip considered as invitation?")
    # is_ticket_provided = fields.Selection(
    #     [('yes', 'Yes'), ('no', 'No')], default='no',
    #     string="Is your ticket provided (not by our company)?")
    # is_accommodation_provided = fields.Selection(
    #     [('yes', 'Yes'), ('no', 'No')], default='no',
    #     string="Is your accommodation provided (not by our company)?")
    # book_ticket = fields.Selection(
    #     [('yes', 'Yes'), ('no', 'No')], default='no',
    #     string="Would you like the HR department to book your ticket/s?")
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id, string='Company')
    business_trip_policy_id = fields.Many2one(
        'service.configuration.panel', string='Trip Type')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', track_visibility='onchange',
        string="Cost Center")
    about_service = fields.Text(
        string='About The Service',
        related='business_trip_policy_id.about_service')
    submit_message = fields.Text(
        related='business_trip_policy_id.submit_message',
        string='Submit Hint Message', store=True)
    stage_id = fields.Many2one(
        'service.panel.displayed.states', string='States To Be Displayed',
        domain="[('service_type_ids', '=', business_trip_policy_id)]",
        index=True, copy=False)
    state = fields.Selection(
        SERVICE_STATUS, string='Status', readonly=True,
        track_visibility='onchange',
        help='When the Business Trip Request is created the status is '
             '\'Draft\'.\n Then the request will be forwarded based on the '
             'service type configuration.', default='draft')
    endorsement_text = fields.Text(
        related='business_trip_policy_id.endorsement_text',
        string='Endorsement Text',
        readonly=True, copy=False)
    endorsement_required = fields.Boolean(
        string='Endorsement Approved', track_visibility='onchange',
        readonly=1, copy=False, states={'draft': [('readonly', False)]})
    endorsement_for_bt = fields.Boolean(
        related='business_trip_policy_id.endorsement_required',
        store=True,
        string='Endorsement Required for Business Trip')
    # approvals
    bt_submitted_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True, copy=False,
        help='Who requested the service.')
    bt_submit_date = fields.Datetime(string='Submit Date', readonly=True,
                                     copy=False)
    bt_manager_user_id = fields.Many2one(
        'res.users', string='Manager Approval', readonly=True, copy=False)
    bt_manager_approval_date = fields.Datetime(
        string='Manager Approval Date', readonly=True, copy=False)
    bt_vp_user_id = fields.Many2one(
        'res.users', string='VP Approval', readonly=True, copy=False)
    bt_vp_approval_date = fields.Datetime(
        string='VP Approval Date', readonly=True, copy=False)
    bt_hr_user_id = fields.Many2one(
        'res.users', string='HR Approval', readonly=True, copy=False)
    bt_hr_approval_date = fields.Datetime(
        string='HR Approval Date', readonly=True, copy=False)
    bt_budget_user_id = fields.Many2one(
        'res.users', string='Budget Approval', readonly=True, copy=False)
    bt_budget_approval_date = fields.Datetime(
        string='Budget Approval Date', readonly=True, copy=False)
    bt_ceo_user_id = fields.Many2one(
        'res.users', string='CEO Approval', readonly=True, copy=False)
    bt_ceo_approval_date = fields.Datetime(
        string='CEO Approval Date', readonly=True, copy=False)
    bt_final_hr_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    bt_final_hr_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    bt_finance_user_id = fields.Many2one(
        'res.users', string='Final HR Approval', readonly=True, copy=False)
    bt_finance_approval_date = fields.Datetime(
        string='Final HR Approval Date', readonly=True, copy=False)
    bt_rejected_user_id = fields.Many2one(
        'res.users', string='Rejected By', readonly=True, copy=False)
    bt_rejected_date = fields.Datetime(
        string='Rejected Date', readonly=True, copy=False)
    bt_final_approval_date = fields.Datetime(
        'Final Approval Date', readonly=True, copy=False)
    bt_waiting_time = fields.Char(
        compute=_calculate_ongoing_waiting_time,
        string='Waiting Time', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    expected_approval_date_as_sla = fields.Datetime(
        compute=_calculate_expected_approval_date_as_sla,
        string='Expected Approval Date As SLA', method=True, copy=False,
        states={'draft': [('readonly', False)]})
    service_log_ids = fields.One2many('service.log', 'business_trip_id',
                                      'Service Logs')
    service_request_count = fields.Integer('Service Request Count',
                                           store=False,
                                           compute='_count_service_request',
                                           search="search_service_request")
    is_accommodation_provide = fields.Selection([
        ('yes', 'Yes'), ('no', 'NO')],
        string='Dose the accommodation provided ?')
    # additional_services = fields.Boolean('Additional Services')
    # service_request_ids = fields.One2many(
    #     'service.request', 'business_trip_id', string='Service Request')

    # Accounting Information
    accounting_date = fields.Date(string='Accounting Date', copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 copy=False)
    # debit_account_id = fields.Many2one('account.account',
    #                                    string='Debit Account', copy=False)
    credit_account_id = fields.Many2one('account.account',
                                        string='Credit Account', copy=False)
    product_id = fields.Many2one('product.product', string='Product')
    account_move_id = fields.Many2one(
        'account.move', string='Journal Entry', copy=False)
    paid_to_employee = fields.Boolean(string='Paid to Employee', copy=False)
    # Calculation
    bt_allowance_cal_ids = fields.One2many(
        'bt.allowance.cal', 'business_trip_id',
        string='Item')
    # accommodation_amount = fields.Float('Accommodation')
    # per_diem_amount = fields.Float('Per Diem')
    # ticket_amount = fields.Float('Ticket Value')
    # other_amount = fields.Float('Other Amount')
    total_amount = fields.Float('Total Trip Cost',
                                compute='_calculate_total_amount',
                                store=True)
    hr_holidays_id = fields.Many2one('hr.holidays', 'Leave Request')
    proof_required = fields.Boolean(
        related='business_trip_policy_id.proof_required',
        string='Proof Required', store=True)
    business_trip_proof_ids = fields.One2many(
        'business.trip.proof', 'business_trip_id', string='Attachment/s')
    remarks = fields.Text('Remarks')
    budget = fields.Selection([
        ('under_budget', 'Under budget'),
        ('out_budget', 'Out of budget'),
        ('exceptional_out_budget', 'Out of Budget with Exception')],
        string='Budget Status')
    budget_exception_reason = fields.Text(string='Budget Exception Reason')
    is_analytic_acc_diff = fields.Boolean('is Analytic Acc Diff')

    @api.model
    def _calculate_bt_allowances(self):
        """
        calculate accommodation and per diem amount
        :return:
        """
        allowances_cal_list = [(2, x,) for x in self.bt_allowance_cal_ids.ids]
        if self.business_trip_policy_id and self.country_id and \
                self.employee_id.contract_id and \
                self.employee_id.contract_id.grade_level:
            for bt_cal_rec in \
                    self.business_trip_policy_id.business_trip_calculation_ids:
                acc_id = bt_cal_rec.bt_allowance_id.account_id and \
                         bt_cal_rec.bt_allowance_id.account_id.id or False
                if self.employee_id.contract_id.grade_level.id in \
                        bt_cal_rec.grade_level_ids.ids:
                    if bt_cal_rec.bt_countries_group_id:
                        if self.country_id.id in \
                                bt_cal_rec.bt_countries_group_id.\
                                        country_ids.ids:
                            if bt_cal_rec.amount and self.total_request_days:
                                total_amount = bt_cal_rec.amount * \
                                               self.total_request_days
                                allowances_cal_list += [(0, 0, {
                                    'bt_allowance_id':
                                        bt_cal_rec.bt_allowance_id.id,
                                    'per_day_amount': bt_cal_rec.amount,
                                    'amount': total_amount,
                                    'account_id': acc_id,

                                })]
        self.bt_allowance_cal_ids = allowances_cal_list

    # @api.multi
    # def add_total_training_cost(self):
    #     for rec in self:
    #         business_trip_allowance_line_rec = self.env[
    #             'business.trip.allowance'].search([('code', '=', 'TTCOST')],
    #                                               limit=1)
    #         if not business_trip_allowance_line_rec:
    #             raise Warning(_('To Proceed, There should be a type for calculating '
    #                             'the total training cost. \n Kindly contact the HR Team.'))
    #         existing_trip_allowance = [line for line in
    #                                          rec.bt_allowance_cal_ids if
    #                                    line.bt_allowance_id.code == 'TTCOST']
    #         if existing_trip_allowance:
    #             raise Warning(
    #                 _('Already, the training total cost has been before.'))
    #         vals = {
    #             'bt_allowance_id':
    #                 business_trip_allowance_line_rec.id,
    #             'amount': rec.total_training_cost,
    #             'business_trip_id': rec.id,
    #             'account_id': business_trip_allowance_line_rec.account_id
    #                           and
    #                           business_trip_allowance_line_rec.account_id.id
    #                           or False
    #         }
    #         self.env['bt.allowance.cal'].create(vals)

    @api.model
    def get_diff_days(self, f_date, t_date):
        """
        :param f_date:
        :param t_date:
        :return:
        """
        f_date = datetime.strptime(f_date, DEFAULT_SERVER_DATE_FORMAT)
        e_date = datetime.strptime(t_date, DEFAULT_SERVER_DATE_FORMAT)
        delta = e_date - f_date
        return delta.days + 1

    @api.model
    def check_travel_days_validation(self):
        """
        :return:
        """
        if self.trip_departure_date and self.trip_return_date:
            diff_days = self.get_diff_days(
                self.trip_departure_date, self.trip_return_date)
            if diff_days > self.total_trip_days:
                raise Warning(_('Total travel days should not exceed %s days.')
                              % (self.total_trip_days))
            trip_departure_date = False
            trip_return_date = False
            actual_start_date = False
            actual_end_date = False
            if self.trip_departure_date:
                trip_departure_date = datetime.strptime(
                    self.trip_departure_date, DEFAULT_SERVER_DATE_FORMAT)
            if self.trip_return_date:
                trip_return_date = datetime.strptime(
                    self.trip_return_date, DEFAULT_SERVER_DATE_FORMAT)
            if self.actual_start_date:
                actual_start_date = datetime.strptime(
                    self.actual_start_date, DEFAULT_SERVER_DATE_FORMAT)
            if self.actual_end_date:
                actual_end_date = datetime.strptime(
                    self.actual_end_date, DEFAULT_SERVER_DATE_FORMAT)
            if actual_start_date and trip_departure_date:
                if actual_start_date < trip_departure_date:
                    raise Warning(_('Actual start date should not be less '
                                    'than the trip departure date.'))
            if actual_end_date and trip_return_date:
                if actual_end_date > trip_return_date:
                    raise Warning(_('Actual end date should not be greater '
                                    'than the trip return date.'))
            if actual_start_date and actual_end_date:
                if actual_end_date < actual_start_date:
                    raise Warning(_('Actual start date should not be greater '
                                    'than the Actual end date.'))
            if trip_departure_date and trip_return_date:
                if trip_return_date < trip_departure_date:
                    raise Warning(_('Trip departure date should not be '
                                    'greater than the trip return date.'))

    @api.onchange('actual_start_date', 'actual_end_date')
    def onchange_actual_dates(self):
        """
        :return:
        """
        if self.actual_start_date:
            self.trip_departure_date = self.actual_start_date
        if self.actual_end_date:
            self.trip_return_date = self.actual_end_date

    @api.onchange('trip_departure_date', 'trip_return_date')
    def onchange_trip_dates(self):
        if self.trip_departure_date and self.trip_return_date:
            self.check_travel_days_validation()

    @api.constrains('trip_departure_date', 'trip_return_date')
    def _all_validation_on_travel_days(self):
        for rec in self:
            rec.check_travel_days_validation()
            domain = [
                ('trip_departure_date', '<=', rec.trip_departure_date),
                ('trip_return_date', '>=', rec.trip_return_date),
                ('employee_id', '=', rec.employee_id.id),
                ('id', '!=', rec.id),
                ('business_trip_policy_id', '=',
                 rec.business_trip_policy_id.id),
                ('state', 'not in', ['rejected']),
            ]
            ntrip = self.search_count(domain)
            if ntrip:
                raise Warning(_('You can not have 2 business trip that '
                                'overlaps on same day!'))

    @api.onchange('country_id', 'state_id', 'total_request_days')
    def onchange_state_country(self):
        """
        onchange on state or country
        :return:
        """
        if self.country_id or self.state_id:
            self._calculate_bt_allowances()

    @api.model
    def _get_business_trip_policy(self):
        if not self.company_id or not self.company_id.business_trip_policy_id:
            raise Warning(_('There is no an active policy for the business '
                            'trip, For more information, Kindly contact '
                            'the HR Team.'))
        return self.company_id.business_trip_policy_id

    @api.onchange('company_id')
    def onchange_company_id(self):
        business_trip_policy = self._get_business_trip_policy()
        if not business_trip_policy:
            raise Warning(_('You are not allowed to apply for this request '
                            'until the business trip policy has been '
                            'applied.'))
        self.business_trip_policy_id = business_trip_policy.id

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

    @api.onchange('account_analytic_id')
    def onchange_account_analytic_id(self):
        """
        is account_analytic_id different
        :return:
        """
        is_analytic_acc_diff = False
        if self.account_analytic_id and self.job_id and \
                self.job_id.analytic_account_id:
            if self.account_analytic_id.id != \
                    self.job_id.analytic_account_id.id:
                is_analytic_acc_diff  = True
        self.is_analytic_acc_diff = is_analytic_acc_diff

    @api.model
    def update_account_information(self):
        """
        :return:
        """
        if self.business_trip_policy_id:
            self.product_id = self.business_trip_policy_id.product_id and \
                self.business_trip_policy_id.product_id.id or False
            self.journal_id = self.business_trip_policy_id.journal_id and \
                self.business_trip_policy_id.journal_id.id or False
            self.credit_account_id = \
                self.business_trip_policy_id.journal_id and \
                self.business_trip_policy_id.journal_id\
                    .default_credit_account_id or False
            # self.debit_account_id = \
            #     self.business_trip_policy_id.product_id and \
            #     self.business_trip_policy_id.product_id.\
            #         property_account_expense_id or False

    @api.onchange('business_trip_policy_id')
    def onchange_business_trip_policy(self):
        """
        :return: onchange business trip.
        """
        res = {'state_id': []}
        if self.business_trip_policy_id:
            self.state_id = False
            self.country_id = False
            if self.business_trip_policy_id.states_to_display_ids:
                stage_rec = self.business_trip_policy_id.states_to_display_ids[0]
                stage_list = filter(None, map(
                    lambda x: x.case_default and x,
                    self.business_trip_policy_id.states_to_display_ids))
                if stage_list:
                    stage_rec = stage_list[0]
                self.stage_id = stage_rec.id
            # account information
            self.update_account_information()
            proof_lst = []
            for proof_rec in self.business_trip_proof_ids:
                proof_lst.append((2, proof_rec.id))
            if self.proof_required:
                for line in self.business_trip_policy_id.service_proof_ids:
                    proof_lst.append((0, 0, {
                        'name': line.name, 'description': line.description,
                        'mandatory': line.mandatory
                    }))
            self.business_trip_proof_ids = proof_lst
            if self.business_trip_policy_id.display_internal_city_only:
                if self.company_id.country_id:
                    res['state_id'] = [
                        ('country_id', '=', self.company_id.country_id.id)]
        # Calculate amount
        self._calculate_bt_allowances()
        return {'domain': res}

    @api.onchange('state_id')
    def onchange_state_id(self):
        """
        update Country accordingly
        :return:
        """
        self.country_id = False
        if self.state_id and self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.model
    def create(self, vals):
        """
        :return:
        """
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'business.trip')
        res = super(OrgBusinessTrip, self).create(vals)
        return res

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if self.business_trip_policy_id and \
                self.business_trip_policy_id.states_to_display_ids:
            stage_rec = self.business_trip_policy_id.states_to_display_ids[0]
            stage_list = filter(None, map(
                lambda x: x.case_default and x,
                self.business_trip_policy_id.states_to_display_ids))
            if stage_list:
                stage_rec = stage_list[0]
            self.stage_id = stage_rec.id
        default.update({'stage_id': stage_rec.id})
        return super(OrgBusinessTrip, self).copy(default)

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
            if service.business_trip_policy_id.mngr_approval:
                req_approvals.append('mngr_approval')
            if service.business_trip_policy_id.vp_approval:
                req_approvals.append('vp_approval')
            if service.business_trip_policy_id.hr_approval:
                req_approvals.append('hr_approval')
            if service.business_trip_policy_id.budget_approval:
                req_approvals.append('budget_approval')
            if service.business_trip_policy_id.hr_approval:
                req_approvals.append('final_hr_approval')
            if service.business_trip_policy_id.ceo_approval:
                req_approvals.append('ceo_approval')
            if service.business_trip_policy_id.finance_approval:
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
        elif self.is_transition_allowed('final_hr_approval'):
            self.action_submit_to_hr_review()
        elif self.is_transition_allowed('ceo_approval'):
            self.action_submit_to_ceo_approval()
        elif self.is_transition_allowed('finance_processing'):
            self.action_submit_to_final_finance_processing()
        else:
            return False
        return True

    @api.multi
    def _get_business_trip_dest_state(self, service):
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
    def _check_business_trip_restrictions(self):
        for service in self:
            ir_obj = self.env['ir.attachment']
            attachment_mandatory = \
                service.business_trip_policy_id.attachment_mandatory
            if attachment_mandatory:
                existing_attachment = ir_obj.search([
                    ('res_id', '=', service.id),
                    ('res_model', '=', service._name)])
                if not existing_attachment:
                    raise Warning(
                        _('You are not allowed to submit the request without '
                          'attaching a document.\n For attaching a document: '
                          'press save then attach a document.'))
            if service.business_trip_policy_id.endorsement_required and not \
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
            ('model_id.model', '=', 'org.business.trip')])
        if stage_ids:
            stage_id = stage_ids[0]
        return stage_id

    @api.model
    def _get_business_trip_approval_info(self, service, dest_state):
        current_state = service.state
        stage_id = self._get_dest_related_stages(dest_state)
        if not stage_id:
            raise Warning(_(
                "There is no related stage for %s") % (dest_state))
        result = {'stage_id': stage_id.id}
        if current_state == 'draft':
            result.update({'state': dest_state,
                           'bt_submitted_by': self.env.user.id,
                           'bt_submit_date': self._get_current_datetime()})
        elif current_state == 'mngr_approval':
            result.update(
                {'state': dest_state,
                 'bt_manager_user_id': self.env.user.id,
                 'bt_manager_approval_date': self._get_current_datetime()})
        elif current_state == 'vp_approval':
            result.update(
                {'state': dest_state,
                 'bt_vp_user_id': self.env.user.id,
                 'bt_vp_approval_date': self._get_current_datetime()})
        elif current_state == 'hr_approval':
            result.update(
                {'state': dest_state,
                 'bt_hr_user_id': self.env.user.id,
                 'bt_hr_approval_date': self._get_current_datetime()})
        elif current_state == 'budget_approval':
            result.update(
                {'state': dest_state,
                 'bt_budget_user_id': self.env.user.id,
                 'bt_budget_approval_date': self._get_current_datetime()})
        elif current_state == 'ceo_approval':
            result.update(
                {'state': dest_state,
                 'bt_ceo_user_id': self.env.user.id,
                 'bt_ceo_approval_date': self._get_current_datetime()})
        elif current_state == 'final_hr_approval':
            result.update(
                {'state': dest_state,
                 'bt_final_hr_user_id': self.env.user.id,
                 'bt_final_hr_approval_date': self._get_current_datetime()})
        elif current_state == 'finance_processing':
            result.update(
                {'state': dest_state,
                 'bt_finance_user_id': self.env.user.id,
                 'bt_finance_approval_date': self._get_current_datetime()})
        elif current_state == 'rejected':
            result.update({'state': dest_state})
        return result

    @api.multi
    def _action_create_leave_request(self):
        """
        :return:
        """
        leave_type = self.env['hr.holidays.status'].search([
            ('code', '=', 'BSNSLV')])
        if not leave_type:
            raise Warning(_("Leave type not found with code 'BSNSLV'."))
        name = 'Leave Request From Business Trip : %s' % (self.name)
        leave_rec = self.env['hr.holidays'].create({
            'type': 'remove',
            'employee_id': self.employee_id.id,
            'holiday_status_id': leave_type.id,
            'name': name,
            'date_from': self.trip_departure_date,
            'date_to': self.trip_return_date,
            'real_days': 1,
        })
        # call onchange
        leave_rec.onchange_date()
        # submit request
        leave_rec.holidays_to_manager()
        # hr approved
        leave_rec.to_validate2()
        self.hr_holidays_id = leave_rec.id

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
        for rec in self.business_trip_proof_ids:
            if rec.mandatory and not rec.document:
                raise Warning(
                    _('To proceed,'
                      'Kindly you should attach the files as required '
                      'in the service.'))

    @api.multi
    def _check_user_permissions(self, sign='approve'):
        for rec in self:
            if not rec._check_group(
                    'org_business_trip.group_bt_self_approval_service'):
                if rec.state == 'mngr_approval' and \
                                rec.employee_id.user_id.id == self.env.user.id:
                    raise Warning(_(
                        "Please, Make sure that you have the rights to %s "
                        "your own request.") % (sign))
        return False

    @api.multi
    def action_submit_request(self):
        """
        submit Business Trip request
        :return:
        """
        for rec in self:
            if not rec.business_trip_policy_id:
                raise Warning(
                    _('You are not allowed to apply for this request '
                      'until the business trip policy has been applied.'))
            allow_behalf_req = rec._check_group(
                'org_business_trip.group_bt_on_behalf_of_other')
            if not allow_behalf_req:
                employee_rec = self.env['hr.employee'].search(
                    [('user_id', '=', self._uid)], limit=1)
                if self.employee_id != employee_rec:
                    raise Warning(_('You are not allowed to do this change on '
                                    'behalf of others.'))
            rec.check_for_service_proof()
            rec._check_point_for_all_stage()

    @api.multi
    def action_submit_to_manager(self):
        for service in self:
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                service.write(
                    self._get_business_trip_approval_info(
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
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_approval(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_ceo_approval(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service, dest_state))
                self._action_create_leave_request()
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_budget_approval(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_hr_review(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            if service.budget:
                if service.budget == 'out_budget':
                    raise Warning(_("You cannot"
                                    " proceed with this"
                                    " request because it's"
                                    " out of budget. "))
            else:
                raise Warning(
                    _("You cannot proceed without budget status. "))
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service, dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_finance_processing(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service,
                                                          dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_submit_to_final_finance_processing(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(
                    self._get_business_trip_approval_info(service,
                                                          dest_state))
                self._action_send_email(dest_state)
        return True

    @api.multi
    def action_final_hr_approved(self):
        for service in self:
            self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = self._get_business_trip_dest_state(service)
            if dest_state:
                self.write(self._get_business_trip_approval_info(
                    service, dest_state))
                self.write({
                    'bt_final_approval_date': self._get_current_datetime()
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
            'bt_submitted_by': False,
            'bt_submit_date': False,
            'bt_manager_user_id': False,
            'bt_manager_approval_date': False,
            'bt_vp_user_id': False,
            'bt_vp_approval_date': False,
            'bt_hr_user_id': False,
            'bt_hr_approval_date': False,
            'bt_ceo_user_id': False,
            'bt_ceo_approval_date': False,
            'bt_final_hr_user_id': False,
            'bt_final_hr_approval_date': False,
            'bt_finance_user_id': False,
            'bt_finance_approval_date': False,
            'bt_rejected_user_id': False,
            'bt_rejected_date': False,
            'bt_final_approval_date': False,
        }
        return return_dict

    @api.multi
    def action_business_trip_return(self):
        """
        return business trip request
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = 'draft'
            result = self._get_business_trip_approval_info(
                service, dest_state)
            result.update(self._get_return_dict())
            service.write(result)
            self._action_send_email('return_to_draft')
        return True

    @api.multi
    def action_business_trip_reject(self):
        """
        return business trip reject
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
            dest_state = 'rejected'
            service.write(self._get_business_trip_approval_info(
                service, dest_state))
            self._action_send_email('rejected')

    def _prepare_move_lines(self, move):
        move_lst = []
        generic_dict = {
            'name': self.name,
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

        # Prepared debit entry
        for line in self.bt_allowance_cal_ids:
            if not line.account_id:
                raise Warning(_('Please add all accounts on calculation '
                                'Line.'))
            debit_entry_dict = {
                'account_id': line.account_id,
                'debit': line.amount,
                'analytic_account_id': self.account_analytic_id and
                                       self.account_analytic_id.id or False
            }
            debit_entry_dict.update(generic_dict)
            move_lst.append((0, 0, debit_entry_dict))

        # Prepared credit entry
        credit_entry_dict = {
            'account_id': self.credit_account_id.id,
            'credit': self.total_amount,
        }
        credit_entry_dict.update(generic_dict)
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
        return business trip reject
        :return:
        """
        for service in self:
            # self._check_user_permissions('approve')
            self._check_business_trip_restrictions()
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

    @api.multi
    def action_service_management_request(self):
        """
        Open Service Management
        :return:
        """
        res = self.env['ir.actions.act_window'].for_xml_id(
            'service_management', 'act_all_services_with_reference')
        ctx = {'default_reference_id': str(self._name) + ',' + str(self.id),
               'default_employee_id': self.employee_id.id,
               'linked_with_business_trip': True}
        if self.state != 'draft':
            ctx.update({'create':False,'edit':False,'delete':False})
        res['context'] = ctx
        return res

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
            'org_business_trip.action_bt_request_for_view_all'
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
            'model': 'org.business.trip'
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
            temp_xml_id = 'org_business_trip.bt_request_send_to_manager'
        elif dest_state == 'vp_approval':
            temp_xml_id = 'org_business_trip.bt_request_send_to_vp'
        elif dest_state == 'hr_approval':
            temp_xml_id = 'org_business_trip.bt_request_send_to_hr_approval'
        elif dest_state == 'budget_approval':
            temp_xml_id = \
                'org_business_trip.bt_request_send_to_budget_approval'
        elif dest_state == 'ceo_approval':
            temp_xml_id = 'org_business_trip.bt_request_send_to_ceo'
        elif dest_state == 'final_hr_approval':
            temp_xml_id = \
                'org_business_trip.bt_request_send_to_final_hr_approval'
        elif dest_state == 'finance_processing':
            temp_xml_id = 'org_business_trip.' \
                          'bt_request_send_to_final_finance_processing'
        elif dest_state == 'approved':
            temp_xml_id = 'org_business_trip.bt_request_approved'
        elif dest_state == 'return_to_draft':
            temp_xml_id = 'org_business_trip.bt_request_return'
        elif dest_state == 'rejected':
            temp_xml_id = 'org_business_trip.bt_request_rejected'

        if temp_xml_id:
            self._send_email(temp_xml_id, email_to)
        return True
