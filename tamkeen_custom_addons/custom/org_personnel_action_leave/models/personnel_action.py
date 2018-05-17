from odoo import models, api, fields, _
from odoo.exceptions import Warning
from days360 import get_date_diff_days360
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT


class PersonnelActionType(models.Model):
    _inherit = 'personnel.action.type'

    create_leave_account = fields.Boolean(string='Create Leave Account')
    allocate_balance = fields.Boolean(string='Allocate Balance')


class PersonnelActions(models.Model):
    _inherit = 'personnel.actions'

    def _get_holidays_status(self):
        holidays_status_rec = self.env['hr.holidays.status'].search([(
            'code', '=', 'ANNLV')], limit=1)
        if not holidays_status_rec:
            raise Warning(_('Leave type should have a proper '
                            'configuration for annual leave type code.'))
        return holidays_status_rec

    def _check_employee_leave_account(self):
        leave_account_obj = self.env['employee.leave.summary']
        holidays_status_rec = self._get_holidays_status()
        employee_leave_account = leave_account_obj.search([(
            'employee_id', '=', self.employee_id.id), ('holiday_status_id',
                                                       '=',
                                                       holidays_status_rec.id)])
        return employee_leave_account, holidays_status_rec

    @api.multi
    def submit_for_approval(self):
        for rec in self:
            if rec.action_type_id and rec.action_type_id.create_leave_account:
                employee_leave_account, holiday_status_rec = \
                    rec._check_employee_leave_account()
                if employee_leave_account:
                    raise Warning(
                        _('This employee already have leave account.'))
                if rec.action_type_id.allocate_balance:
                    self._check_employee_ok_for_allocation()
        return super(PersonnelActions, self).submit_for_approval()

    def _check_employee_ok_for_allocation(self):
        if not self.employee_id.initial_employment_date:
            raise Warning(_('Employee should have joining date.'))
        if not self.new_position_id:
            raise Warning(_('This personnel action should have new position.'))
        return True

    def _get_employee_accrual_days(self, employee):
        joining_date = self.employee_id.initial_employment_date
        joining_date = datetime.strptime(joining_date, OE_DATEFORMAT)
        year_end_dt = joining_date.replace(month=12, day=31)
        date_diff = get_date_diff_days360(joining_date, year_end_dt)
        daily_accrual_rate = self.env[
            'hr.holidays']._get_employee_daily_balance(employee)
        return date_diff, daily_accrual_rate

    def _get_employee_leave_balance(self, employee):
        self._check_employee_ok_for_allocation()
        date_diff, daily_accrual_rate = self._get_employee_accrual_days(
            employee)
        return self.env['hr.holidays']._get_emp_accrual_days(date_diff,
                                                   daily_accrual_rate)

    @api.multi
    def button_active(self):
        leave_account_obj = self.env['employee.leave.summary']
        holidays_obj = self.env['hr.holidays']
        for rec in self:
            if rec.action_type_id and rec.action_type_id.create_leave_account:
                employee_leave_account, holiday_status_rec  = rec._check_employee_leave_account()
                if employee_leave_account:
                    raise Warning(
                        _('This employee already have leave account.'))
                else:
                    leave_account_obj.create({'employee_id': self.employee_id.id,
                                              'holiday_status_id':
                                                  holiday_status_rec.id})
                employee_leave_balance = rec._get_employee_leave_balance(
                    rec.employee_id)
                if rec.action_type_id.allocate_balance:
                    holidays_obj.create({'employee_id': self.employee_id.id,
                                         'holiday_status_id':
                                             holiday_status_rec.id,
                                         'number_of_days_temp':
                                             employee_leave_balance,
                                        'type': 'add',
                                         'state': 'validate',
                                         'allocation_type': 'addition'
                                         })
        return super(PersonnelActions, self).button_active()