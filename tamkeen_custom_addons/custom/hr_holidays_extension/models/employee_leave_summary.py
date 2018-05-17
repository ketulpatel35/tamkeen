from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from days360 import get_date_diff_days360


class EmployeeLeaveSummary(models.Model):
    _name = 'employee.leave.summary'
    _description = 'Employee Leave Summary'
    _rec_name = 'employee_id'

    _sql_constraints = [('employee_leave_summary_unique',
                         'UNIQUE(employee_id,holiday_status_id)',
                         'Employee summary Must be unique for per '
                         'Employee per leave type!')]

    @api.multi
    def _get_leave_remaining_balance(self):
        for rec in self:
            rec.real_days = (rec.balance_allocate - (rec.deducted_balance +
                                                     rec.approved_leave +
                                                     rec.locked_balance))

    @api.multi
    def _get_approved_leave(self):
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id', '=', rec.holiday_status_id.id),
                 ('state', '=', 'validate'),
                 ('type', '=', 'remove')])
            for holidays in holidays_rec:
                if holidays.real_days:
                    rec.approved_leave += holidays.real_days

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
                    requested_leave_balance += holiday.real_days
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
        all_days = get_date_diff_days360(s_date, till_date)
        return all_days * self.env[
            'hr.holidays']._get_employee_daily_balance(emp_rec)

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
            rem_bal_out = int((total_allocated_balance) - int(
                total_leave_request) + int(rec.deducted_balance))
            rec.pro_rata_balance = rem_bal_out

    @api.multi
    def action_leave_request(self):
        """
         Leave Request smart button (display record in tree view)
        :return:
        """
        context = dict(self._context)
        domain = []
        holidays_ids = []
        for rec in self:
            holidays_rec = self.env['hr.holidays'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('type', '=', 'remove'), ('holiday_status_id', '=',
                                          rec.holiday_status_id.id)])
            if holidays_rec:
                holidays_ids = holidays_rec.ids
            domain.append(('id', 'in', holidays_ids))
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
    approved_leave = fields.Float(
        compute='_get_approved_leave',
        help='Employee leaves which are approved.',
        string='Approved Leave')
    balance_allocate = fields.Float(
        compute='_get_balance_allocate',
        help='Employee balance left from the leaves allocated.',
        string='Allocated Balance')
    locked_balance = fields.Float(
        compute='_get_locked_balance',
        string='Locked Balance',
        help='Leaves applied by employees which is not approved yet.')
    real_days = fields.Float(
        compute='_get_leave_remaining_balance',
        help='Leave balance of Employee which is available for application.',
        string='Available Balance')
    leaves_count = fields.Integer(string='Leave Request',
                                  compute='_leaves_count')
    deducted_balance = fields.Float(string='Deducted Balance',
                                    compute='_get_deducted_balance')
    pro_rata_balance = fields.Float(string='Pro-Rata Balance',
                                    compute="_get_pro_rata_balance")
    code = fields.Char(string='Holiday Status Code',
                       related='holiday_status_id.code')