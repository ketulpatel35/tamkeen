from odoo import api, models, fields, _
import time
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from odoo.exceptions import Warning


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'


    leave_allocation_batch_id = fields.Many2one('hr.leave.allocation.batch',
                                                string='Leave Allocation '
                                                       'Batch',
                                                ondelete='cascade')
    from_accrual = fields.Boolean(string='Created by Accrual Policy Line',
                                  help='Used to differentiate allocations '
                                       'from accruals and manual allocations')


    allocation_date = fields.Date(string='Allocation Date')


    def _check_minimum_employee_days(self, minimum_employed_days, employee_rec):
        srvc_months, dHire = \
            employee_rec.get_months_service_to_date()[
                employee_rec.id]
        # if accrual_policy.type != 'calendar':
        #     return
        dToday = date.today()
        employed_days = 0
        dCount = dHire
        while dCount < dToday:
            employed_days += 1
            dCount += timedelta(days=+1)
        if minimum_employed_days > employed_days:
            raise Warning(_('The employee is not eligible for the '
                            'allocation unless his/her wroking days '
                            'are greater than the minimum employee '
                            'days'))


    @api.multi
    def holidays_to_manager(self):
        res = super(HrHolidays, self).holidays_to_manager()
        for rec in self:
            if rec.type == 'add':
                maximum_accumulative_balance, minimum_employee_days, \
                current_employee_balance = 0.0, 0.0, 0.0
                if rec.leave_allocation_batch_id:
                    raise Warning(_('You are not allowed to submit this requets '
                                    'unless a related allocation batch has been '
                                    'approved.'))
                if rec.employee_id.job_id:
                    maximum_accumulative_balance = \
                        rec.employee_id.job_id.maximum_accumulative_balance
                    minimum_employee_days = rec.job_id.trial_period
                    rec._check_minimum_employee_days(minimum_employee_days,
                                                     rec.employee_id)
                    emp_leave_balance = self.env[
                        'hr.holidays']._get_employee_balance(
                        rec.holiday_status_id, rec.employee_id)
                    current_employee_balance = emp_leave_balance.get(
                        'current_employee_balance')
                if current_employee_balance >= maximum_accumulative_balance:
                    current_rm_balance = int(current_employee_balance) - int(
                        self.number_of_days_temp)
                    raise Warning(_("The employee is not eligible for the "
                                    "allocation because his/her balance will "
                                    "be greater than the allowed "
                                    "maximum balance. \n Current Remaining "
                                    "Balance: %s day/s \n Maximum Balance: "
                                    "%s day/s.") % (current_rm_balance,
                                                    maximum_accumulative_balance))
        return res


class HrLevaeAllocationBatch(models.Model):
    _name = 'hr.leave.allocation.batch'
    _description = 'Leave Allocation Batch'
    _order = "id desc"

    name = fields.Char(string='Name')
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=time.strftime('%Y-%m-01'))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=str(
                               datetime.now() + relativedelta.relativedelta(
                                   months=+1, day=1, days=-1))[:10])
    leave_type_id = fields.Many2one('hr.holidays.status', string='Leave Type')
    allocation_type = fields.Selection([('manual', 'Manual'), ('accrual',
                                                               'Accrual'),
                                        ('adjustment', 'Adjustment')],
                                       default='accrual')
    allocation_days = fields.Float(string='Alloation Days')
    skip_previous_period_allocation = fields.Boolean(string='Skip Previous '
                                                         'Period '
                                                      'Allocation')
    holidays_ids = fields.One2many('hr.holidays',
                                   'leave_allocation_batch_id',
                                   string='Allocation Requests',
                                   ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self:
                                 self.env.user.company_id.id)
    state = fields.Selection([('draft', 'Draft'), ('confirm',
                                                   'Confirmed'),
                              ('approved', 'Approved'),
                               ('close', 'Closed'), ('cancel', 'Cancelled')],
                              string='State', default='draft')

    @api.onchange('allocation_type')
    def onchange_allocation_type(self):
        for rec in self:
            for line in rec.holidays_ids:
                line.unlink()
            rec.allocation_days = 0.0

    @api.onchange('date_start', 'date_end')
    def onchange_date(self):
        if (self.date_start and self.date_end) and (self.date_start >
                                                        self.date_end):
            raise Warning(
                _('The start date must be anterior to the end date.'))

    @api.multi
    def allocation_approved(self):
        for rec in self:
            for line in rec.holidays_ids:
                line.write({'state': 'validate'})
            rec.write({'state': 'approved'})

    @api.multi
    def allocation_close(self):
        for rec in self:
            rec.write({'state': 'close'})

    @api.multi
    def allocation_cancel(self):
        for rec in self:
            for line in rec.holidays_ids:
                line.write({'state': 'cancel'})
            rec.write({'state': 'cancel'})

    @api.multi
    def reset_to_draft(self):
        for rec in self:
            for line in rec.holidays_ids:
                line.write({'state': 'draft'})
            rec.write({'state': 'draft'})

    @api.multi
    def allocation_confirmed(self):
        for rec in self:
            if not rec.holidays_ids:
                raise Warning(_('You should have at least one line.'))
            rec.write({'state': 'confirm'})

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_('You cannot delete the records in draft '
                                'state.'))
        super(HrLevaeAllocationBatch, self).unlink()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        employee_ids = []
        skip_employee_lst = []
        holidays_obj = self.env['hr.holidays']
        if context.get('active_id') and context.get('model') == 'hr.leave.allocation.batch':
            batch_rec = self.env['hr.leave.allocation.batch'].browse(
                context.get(
                'active_id'))
            # if batch_rec.skip_previous_period_allocation:
            if batch_rec.skip_previous_period_allocation:
                holidays_rec = holidays_obj.search([('allocation_date', '>=',
                                                     batch_rec.date_start),
                                                    ('allocation_date', '<=',
                                                     batch_rec.date_end),
                                                    ('type', '=', 'add')])
                for holiday in holidays_rec:
                    skip_employee_lst.append(holiday.employee_id.id)
            for line in batch_rec.holidays_ids:
                employee_ids.append(line.employee_id.id)
        args.append(('id', 'not in', list(set(employee_ids +
                                              skip_employee_lst))))
        return super(HrEmployee, self).search(args, offset, limit, order,
                                              count=count)