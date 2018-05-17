from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
# from days360 import get_date_diff_days360


class EmployeeLeaveSummary(models.Model):
    _name = 'employee.leave.summary'
    _description = 'Employee Leave Summary'
    _rec_name = 'employee_id'

    _sql_constraints = [('employee_leave_summary_unique',
                         'UNIQUE(employee_id,holiday_status_id)',
                         'Employee summary Must be unique for per '
                         'Employee per leave type!')]

    @api.multi
    def _get_allocate_leave(self):
        # for rec in self:
        return 0
            # holidays_rec = self.env['hr.holidays'].search([
            #     ('employee_id', '=', rec.employee_id.id),
            #     ('holiday_status_id', '=', rec.holiday_status_id.id),
            #     ('state', '=', 'validate'),
            #     ('type', '=', 'add'),
            #     ('allocation_type', '=', 'addition')
            #     # ('create_date', '>=', start_date_str),
            #     # ('create_date', '<', end_date_str)
            # ])

            # We need to add filter based on employe contract policy
            # if rec.employee_id and \
            #         rec.employee_id.contract_id and \
            #         rec.employee_id.contract_id.policy_group_id:
            #     accrual_rec = \
            #         self.env['hr.policy.line.accrual'].search([
            #             ('accrual_id.holiday_status_id.id', '=',
            #              rec.holiday_status_id.id)], limit=1)
            #     if accrual_rec and not (len(accrual_rec.ids) > 1):
            #         yearly_accrual_rate = accrual_rec.accrual_rate
            #         rec.yearly_allocate_leave = yearly_accrual_rate
            # for holidays in holidays_rec:
            #     if holidays.number_of_days_temp:
            #         rec.allocate_leave += holidays.number_of_days_temp

    @api.multi
    def _get_leave_remaining_balance(self):
        future_balance_value = 0.0
        allow_future_balance = False
        remaining_balance = 0.0
        holiday_obj = self.env['hr.holidays']
        for rec in self:
            # holidays_status_rec = self.env['hr.holidays.status'].search(
            #     [('id', '=', rec.holiday_status_id.id)])
            # if holidays_status_rec:
            #     remaining_leave_balance = holidays_status_rec.get_days(
            #         rec.employee_id.id)
            #     if remaining_leave_balance:
            #         remaining_balance = remaining_leave_balance.get(
            #             holidays_status_rec.id).get('remaining_leaves')
            #     allow_future_balance = holidays_status_rec.allow_future_balance
            # if allow_future_balance:
            #     future_balance_value =\
            #         holiday_obj._calculate_emp_future_accrued_days(
            #             rec.employee_id, False)
            rec.real_days = (rec.balance_allocate - (rec.deducted_balance +
                                                     rec.approved_leave +
                                                     rec.locked_balance))
            # rec.real_days = remaining_balance + future_balance_value

    @api.multi
    def _get_approved_leave(self):
        # start_date = datetime.today() + relativedelta(month=1, day=1)
        # end_date = datetime.today() + relativedelta(month=12, day=31)
        # start_date_str = datetime.strftime(start_date, OE_DATETIMEFORMAT)
        # end_date_str = datetime.strftime(end_date, OE_DATETIMEFORMAT)
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id', '=', rec.holiday_status_id.id),
                 ('state', '=', 'validate'),
                 ('type', '=', 'remove')])
                 # ('work_resumption_done', '=', False),
                 # ('date_from', '>=', start_date_str),
                 # ('date_to', '<', end_date_str)
            # availed_leave = self.env['work.resumption'].search(
            #     [('holiday_status_id', '=', rec.holiday_status_id.id),
            #      ('employee_id', '=', rec.employee_id.id),
            #      ('state', '=', 'validate'),
            #      ('actual_date_from', '>=', start_date_str),
            #      ('actual_date_to', '<', end_date_str)])
            # for availed in availed_leave:
            #     if availed.actual_number_of_leave_days:
            #         rec.availed_leave += availed.actual_number_of_leave_days
            for holidays in holidays_rec:
                if holidays.real_days:
                    rec.approved_leave += holidays.real_days

    @api.multi
    def _get_applied_leave(self):
        start_date = datetime.today() + relativedelta(month=1, day=1)
        end_date = datetime.today() + relativedelta(month=12, day=31)
        start_date_str = datetime.strftime(start_date, OE_DATETIMEFORMAT)
        end_date_str = datetime.strftime(end_date, OE_DATETIMEFORMAT)
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id', '=', rec.holiday_status_id.id),
                 ('state', 'not in',
                  ('leave_approved', 'validate', 'draft', 'cancel', 'refuse')),
                 ('type', '=', 'remove'),
                 ('date_from', '>=', start_date_str),
                 ('date_to', '<',   end_date_str)])
            for holidays in holidays_rec:
                if holidays.number_of_days_temp:
                    rec.applied_leave += holidays.number_of_days_temp

    @api.multi
    def _get_locked_balance(self):
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search(
                [
                    ('state',
                     'not in',
                     ('draft',
                      'refuse',
                      'cancel',
                      'validate')),
                    ('employee_id',
                     '=',
                     rec.employee_id.id),
                    ('holiday_status_id',
                     '=',
                     rec.holiday_status_id.id),
                    ('type',
                     '=',
                     'remove')])
            for holidays in holidays_rec:
                if holidays.real_days:
                    rec.locked_balance += holidays.real_days

    @api.multi
    def _get_balance_allocate(self):
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('type', '=', 'add'),
                ('allocation_type', '=', 'addition')
            ])
            for holidays in holidays_rec:
                if holidays.number_of_days_temp:
                    rec.balance_allocate += holidays.number_of_days_temp
            # rec.balance_allocate += rec.allocate_leave
            # rec.balance_allocate += (rec.opening_balance +
            #                          rec.allocate_leave) - \
            #                         (rec.approved_leave + rec.availed_leave)

    @api.multi
    def _get_deducted_balance(self):
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('type', '=', 'add'),
                ('allocation_type', '=', 'deduction')
            ])
            for holidays in holidays_rec:
                if holidays.number_of_days_temp:
                    rec.deducted_balance += holidays.number_of_days_temp

    @api.multi
    def _get_yearly_balance(self):
        for rec in self:
            rec.yearly_balance += (rec.opening_balance +
                                   rec.yearly_allocate_leave) - \
                                  (rec.approved_leave + rec.availed_leave)

    @api.model
    def _get_total_leave_request(self, emp_rec, holiday_status_rec, till_date):
        """
        :param emp_rec:
        :param holiday_status_rec:
        :return:
        """
        state_list = ('draft', 'refuse', 'cancel')
        requested_leave_balance = 0.0
        holidays_rec = self.env['hr.holidays'].search([
            ('state', 'not in', state_list), ('employee_id', '=', emp_rec.id),
            ('holiday_status_id', '=', holiday_status_rec.id),
            ('type', '=', 'remove')])
        for holiday in holidays_rec:
            to_date = datetime.strptime(holiday.date_to.split(' ')[0],
                                        DEFAULT_SERVER_DATE_FORMAT).date()
            if to_date <= till_date:
                if holiday.number_of_days_temp:
                    requested_leave_balance += holiday.number_of_days_temp
            else:
                from_date = datetime.strptime(
                    holiday.date_from.split(' ')[0],
                    DEFAULT_SERVER_DATE_FORMAT).date()
                if from_date <= till_date <= to_date:
                    if holiday.number_of_days_temp:
                        data_vals = holiday.count_number_of_days_temp(
                            from_date, till_date)
                        if data_vals:
                            requested_leave_balance += data_vals.get(
                                'real_days')
        return requested_leave_balance

    @api.model
    def get_allocated_balance_today_outside(self, emp_rec, till_date):
        if not emp_rec.initial_employment_date:
            return False
        s_date = datetime.strptime(emp_rec.initial_employment_date,
                                   DEFAULT_SERVER_DATE_FORMAT).date()
        all_days = 0
        # all_days = get_date_diff_days360(s_date, till_date)
        return all_days * self.env['hr.holidays']._get_employee_daily_balance()

    @api.multi
    def _get_pro_rata_balance(self):
        for rec in self:
            to_date = self.departure_date
            if not to_date:
                to_date = str(datetime.today().date())
            till_date = datetime.strptime(to_date,
                                          DEFAULT_SERVER_DATE_FORMAT).date()
            total_allocated_balance = rec.get_allocated_balance_today_outside(
                rec.employee_id, till_date)
            total_leave_request = rec._get_total_leave_request(
                rec.employee_id, rec.holiday_status_id, till_date)
            rem_bal_out = int(total_allocated_balance) - int(total_leave_request)
            rec.pro_rata_balance = rem_bal_out

    @api.multi
    def action_leave_request(self):
        """
         Leave Request smart button (display record in tree view)
        :return:
        """
        context = dict(self._context)
        domain = []
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('type', '=', 'remove'), ('holiday_status_id', '=',
                                          rec.holiday_status_id.id)])
            if holidays_rec:
                domain.append(('id', 'in', holidays_rec.ids))
            return {
                'name': 'Leave Requests',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'hr.holidays',
                'target': 'current',
                'context': context,
                'domain': domain
            }

    @api.multi
    def _leaves_count(self):
        Holidays = self.env['hr.holidays']
        for rec in self:
            rec.leaves_count = Holidays.search_count(
                [('employee_id', '=', rec.employee_id.id),
                 ('type', '=', 'remove'),
                 ('holiday_status_id', '=', rec.holiday_status_id.id)])

    def _get_last_sick_date(self):
        date_list = []
        first_requested_date = False
        holidays_rec = self.env['hr.holidays'].\
            search([('employe_id', '=', self.employee_id.id),
                    ('holiday_status_id', '=', self.holiday_status_id.id),
                    ('type', '=', 'remove')
                    ])
        for holiday in holidays_rec:
            date_list.append(datetime.strptime(holiday.date_from, OE_DATETIMEFORMAT))
        if len(date_list) == 1:
            return date_list[0]
        else:
            min_date = min(date_list)
            # for holiday in holidays_rec:

    @api.multi
    def _get_first_request_date(self):
        for rec in self:
            rec.first_request_date = False

    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_company_id = fields.Char(string='Employee ID',
                         related='employee_id.f_employee_no')
    job_id = fields.Many2one('hr.job', string='Position',
                             related='employee_id.job_id')
    department_id = fields.Many2one('hr.department',
                                    related='employee_id.department_id',
                                    string='Organization Unit', readonly=True,
                                    store=True)
    join_date = fields.Date(related='employee_id.initial_employment_date',
                            string='Join Date')
    departure_date = fields.Date(string='Departure Date',
                                 help='The last day of the '
                                      'employee in the company.')
    holiday_status_id = fields.Many2one('hr.holidays.status',
                                        string='Leave Type')
    contract_id = fields.Many2one('hr.contract',
                                  related='employee_id.contract_id',
                                  string='Current Contract',
                                  help='Latest contract of the employee')
    opening_balance = fields.Float(string='Opening Balance',
                                   help='Employee opening leave balance for '
                                        'the current year.')
    yearly_allocate_leave = fields.Float(
        compute='_get_allocate_leave',
        string='Yearly Allocate',
        help='Employee leaves allocated for the whole year.')
    allocate_leave = fields.Float(
        compute='_get_allocate_leave',
        string='Allocated Leave',
        help='Leaves balance which Employee is eligible to apply.')
    approved_leave = fields.Float(
        compute='_get_approved_leave',
        help='Employee leaves which are approved.',
        string='Approved Leave')
    availed_leave = fields.Float(
        compute='_get_approved_leave',
        string='Availed Leave',
        help='Leaves already availed by the User after approval.')
    balance_allocate = fields.Float(
        compute='_get_balance_allocate',
        help='Employee balance left from the leaves allocated.',
        string='Allocated Balance')
    yearly_balance = fields.Float(
        compute='_get_yearly_balance',
        help='Employee leaves closing balance for the year.',
        strig='Yearly Balance')
    applied_leave = fields.Float(
        compute='_get_applied_leave',
        string='Applied Leave')
    locked_balance = fields.Float(
        compute='_get_locked_balance',
        string='Locked Balance',
        help='Leaves applied by employees which is not approved yet.')
    real_days = fields.Float(
        compute='_get_leave_remaining_balance',
        help='Leave balance of Employee which is available for application.',
        string='Available Balance')
    leaves_count = fields.Integer(string='Leave Request', compute='_leaves_count')
    deducted_balance = fields.Float(string='Deducted Balance',
                                    compute='_get_deducted_balance')
    pro_rata_balance = fields.Float(string='Pro-Rata Balance', compute="_get_pro_rata_balance")
    first_request_date = fields.Date(string='First Request Date',
                                     compute='_get_first_request_date')
    code = fields.Char(string='Holiday Status Code',
                       related='holiday_status_id.code')

    # @api.model
    # def _cron_employee_leave_summary(self):
    #     employee_summary = self.search([])
    #     employee_lst = []
    #     for employee_summ in employee_summary:
    #         employee_lst.append(employee_summ.employee_id.id)
    #     employee_lst = list(set(employee_lst))
    #     employee_rec = self.env['hr.employee'].search([])
    #     for employee in employee_rec:
    #         if employee.id not in employee_lst:
    #             if employee.contract_id and employee.contract_id.grade_level:
    #                 for holiday in employee.contract_id\
    #                         .grade_level.holidays_status_ids:
    #                     self.create({'employee_id': employee.id,
    #                                  'contract_id': employee.contract_id.id,
    #                                  'holiday_status_id': holiday.id})
    #         else:
    #             if employee.contract_id and employee.contract_id.grade_level:
    #                 for holiday in employee.contract_id.grade_level\
    #                         .holidays_status_ids:
    #                     exist_rec = self.search([('employee_id', '=',
    #                                               employee.id),
    #                                              ('holiday_status_id', '=',
    #                                               holiday.id)])
    #                     if not exist_rec:
    #                         self.create({'employee_id': employee.id,
    #                                      'contract_id':
    #                                          employee.contract_id.id,
    #                                      'holiday_status_id': holiday.id})
