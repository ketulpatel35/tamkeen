import datetime
from odoo import fields, models, api, _
from openerp.tools.translate import _
from hijri import Convert_Date
from days360 import get_date_diff_days360
from odoo.exceptions import ValidationError


class HrHolidaysCalculator(models.TransientModel):
    _name = 'hr.holidays.calculator'
    _description = "Holidays Calculator"

    employee_id = fields.\
        Many2one('hr.employee',
                 string='Employee',
                 default=lambda self:
                 self.env['hr.employee'].
                 search([('user_id', '=', self._uid)],
                        limit=1) or False)
    allocate_balance = fields.Boolean(string='Allocate Balance?')
    holiday_status_id = fields.\
        Many2one("hr.holidays.status", string="Leave Type")
    previous_leaves_ids = fields.\
        One2many('hr.holidays', 'employee_id', string='Taken Leaves')
    allocated_leaves_ids = fields.\
        One2many('hr.holidays', 'employee_id', string='Allocated Leaves')
    date_from = fields.Date(string='Start Date')
    hijri_date_from = fields.Char(string='Start Hijri Date')
    date_to = fields.\
        Date(string='End Date',
             default=lambda *a:
             (datetime.datetime(datetime.date.today()
                                .year, 12, 31).date()))
    hijri_date_to = fields.Char(string='End Hijri Date')
    taken_leave_balance = fields.\
        Float(string='Taken Leaves',
              help='Total number of the approved leave requests.')
    allocated_leave_balance = fields.\
        Float(string='Allocated Leaves',
              help='Total number of the allocated approved leave balance.')
    deserved_balance = fields.\
        Float(string='Deserved Balance',
              help='The total number of'
                   ' leave balance this'
                   ' employee deserve'
                   ' within the selected'
                   ' period.')
    leave_max_days = fields\
        .Float(string='Max Annual Leave Days',
               help='The maximum leave balance'
                    ' to be allocated for'
                    ' this employee based'
                    ' on the HR policy.')
    warning_message = fields.Text(string='Warning')

    @api.onchange('hijri_date_from', 'hijri_date_to')
    def onchange_hijri_date(self):
        if self.hijri_date_from:
            self.date_from =\
                Convert_Date(self.hijri_date_from, 'islamic', 'english')
        if self.hijri_date_to:
            self.date_to =\
                Convert_Date(self.hijri_date_to, 'islamic', 'english')

    @api.multi
    def _check_contract(self):
        for record in self:
            if record.employee_id:
                contract_pool = self.env['hr.contract']
                contract_ids =\
                    contract_pool.search([
                        ('employee_id', '=', record.employee_id.id)])
                if contract_ids:
                    return True
                else:
                    return False

    @api.onchange('employee_id', 'allocate_balance')
    def onchange_allocate_balance(self):
        if self.allocate_balance and self.employee_id:
            self.date_from =\
                self.employee_id.initial_employment_date
            self.date_to =\
                datetime.datetime(datetime.date.today().year, 12, 31)
        elif self.employee_id\
                and not self.allocate_balance:
            self.warning_message = ''

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        allocate_balance, warning_message = False, ''
        previous_leaves_ids, allocated_leaves_ids = False, False
        if self.employee_id:
            if self._check_contract():
                holidays_pool = self.env['hr.holidays']
                previous_leaves_ids =\
                    holidays_pool.search([
                        ('employee_id', '=', self.employee_id.id),
                        ('type', '=', 'remove')])
                allocated_leaves_ids =\
                    holidays_pool.search([
                        ('employee_id', '=', self.employee_id.id),
                        ('type', '=', 'add')])
                if not allocated_leaves_ids:
                    allocate_balance = True
            else:
                warning_message =\
                    "The selected employee doesn't" \
                    " have any contracts," \
                    " Please create a contract for him/her."
                allocate_balance = True
            self.previous_leaves_ids = previous_leaves_ids
            self.allocated_leaves_ids = allocated_leaves_ids
            self.taken_leave_balance = False
            self.allocated_leave_balance = False
            self.allocate_balance = allocate_balance
            self.warning_message = warning_message

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        taken_leave_balance, allocated_leave_balance = 0, 0
        previous_leaves_ids, allocated_leaves_ids = False, False
        warning_message = ''
        holi_status_obj = self.env['hr.holidays.status']
        holidays_pool = self.env['hr.holidays']
        allocated_where_clause =\
            [('employee_id', '=', self.employee_id.id),
             ('type', '=', 'remove')]
        previous_where_clause =\
            [('employee_id', '=', self.employee_id.id),
             ('type', '=', 'add')]
        if self.allocate_balance is True:
            allocate_balance = True
        else:
            allocate_balance = False
        if self.holiday_status_id and self.employee_id:
            allocated_where_clause.\
                append(('holiday_status_id', '=', self.holiday_status_id.id))
            previous_where_clause.\
                append(('holiday_status_id', '=', self.holiday_status_id.id))
            previous_leaves_ids =\
                holidays_pool.search(allocated_where_clause)
            allocated_leaves_ids =\
                holidays_pool.search(previous_where_clause)
            leaves_bal =\
                holi_status_obj.get_days(self.employee_id.id)
            taken_leave_balance =\
                leaves_bal.get('leaves_taken')
            allocated_leave_balance =\
                leaves_bal.get('max_leaves')
        if not self.holiday_status_id:
            previous_leaves_ids =\
                holidays_pool.search(allocated_where_clause)
            allocated_leaves_ids =\
                holidays_pool.search(previous_where_clause)
            if not allocated_leaves_ids:
                allocate_balance = True
                warning_message =\
                    "There is no allocation" \
                    " balance for the selected leave type."
        self.previous_leaves_ids = previous_leaves_ids
        self.allocated_leaves_ids = allocated_leaves_ids
        self.taken_leave_balance = taken_leave_balance
        self.allocated_leave_balance = allocated_leave_balance
        self.allocate_balance = allocate_balance
        self.warning_message = warning_message

    @api.onchange('date_to',
                  'date_from',
                  'employee_id',
                  'leave_max_days',
                  'allocate_balance')
    def onchange_leave_max_days(self):
        return self.\
            onchange_date(self.date_to,
                          self.date_from,
                          self.leave_max_days,
                          self.allocate_balance)

    # def get_allocation_values(self, date_from, date_to, leave_max_days):
    #     start_date = \
    #         datetime.datetime.strptime(date_from[:10], '%Y-%m-%d').date()
    #     end_date = \
    #         datetime.datetime.strptime(date_to[:10], '%Y-%m-%d').date()
    #     date_diff = \
    #         get_date_diff_days360(start_date, end_date) or 0.0
    #     daily_accrual_rate = \
    #         leave_max_days / 12 / 30
    #     deserved_balance = \
    #         date_diff * daily_accrual_rate or 0.0
    #     self.hijri_date_from = \
    #         Convert_Date(date_from, 'english', 'islamic')
    #     self.hijri_date_to = \
    #         Convert_Date(date_to, 'english', 'islamic')
    #     self.deserved_balance = deserved_balance
    #     self.warning_message = False

    def onchange_date(self,
                      date_to,
                      date_from,
                      leave_max_days,
                      allocate_balance):
        if (date_from and date_to) and (date_from > date_to):
            raise ValidationError(
                _("The start date must be anterior to the end date."))
        # DATETIME_FORMAT = "%Y-%m-%d" #tools.DEFAULT_SERVER_DATETIME_FORMAT
        if date_from and date_to and leave_max_days and allocate_balance:
            start_date =\
                datetime.datetime.strptime(date_from[:10], '%Y-%m-%d').date()
            end_date =\
                datetime.datetime.strptime(date_to[:10], '%Y-%m-%d').date()
            date_diff =\
                get_date_diff_days360(start_date, end_date) or 0.0
            daily_accrual_rate =\
                leave_max_days / 12 / 30
            deserved_balance =\
                date_diff * daily_accrual_rate or 0.0
            self.hijri_date_from =\
                Convert_Date(date_from, 'english', 'islamic')
            self.hijri_date_to =\
                Convert_Date(date_to, 'english', 'islamic')
            self.deserved_balance = deserved_balance
            self.warning_message = False

    @api.multi
    def allocate_initial_leave_balance(self):
        for record in self:
            if self._check_contract():
                leave_allocation = {
                    'name': 'Auto Leave Allocation',
                    'type': 'add',
                    'employee_id': record.employee_id.id,
                    'number_of_days_temp': record.deserved_balance,
                    'holiday_status_id': record.holiday_status_id.id,
                }
                self.env['hr.holidays'].create(leave_allocation)
            else:
                raise ValidationError(
                    _("The selected employee doesn't"
                      " have any contracts, Please"
                      " create a contract for him/her."))
