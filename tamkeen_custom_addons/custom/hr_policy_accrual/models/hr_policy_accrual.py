from datetime import datetime, date, timedelta
from odoo import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT


leave_allocat = 0.0


class hr_accrual_job(models.Model):
    _name = 'hr.policy.line.accrual.job'
    _description = 'Accrual Policy Line Job Run'

    name = fields.Date(string='Date')
    execution_time = fields.Datetime(string='Execution Date/Time')
    policy_line_id = fields.Many2one('hr.policy.line.accrual',
                                     string='Accrual Policy Line')
    accrual_line_ids = fields.Many2many('hr.accrual.line',
                                        'hr_policy_job_accrual_line_rel',
                                        'job_id',
                                        'accrual_line_id', string='Accrual '
                                                                  'Lines')
    holiday_ids = fields.Many2many('hr.holidays',
                                   'hr_policy_job_holiday_rel', 'job_id',
                                   'holiday_id',
                                   string='Leave Allocation Requests')


class hr_policy(models.Model):
    _name = 'hr.policy.accrual'
    _description = 'Accrual Policy'
    _order = 'date desc'

    name = fields.Char(string='Name')
    date = fields.Date(string='Effective Date')
    line_ids = fields.One2many('hr.policy.line.accrual', 'policy_id',
                               string='Policy Lines')

    # Return records with latest date first
    # @api.multi
    # def _get_leave_balance(self, leave_type_id, employee_id):
    #     # holi_status_obj = self.env['hr.holidays.status']
    #     if leave_type_id and employee_id:
    #         leaves_bal = leave_type_id.get_days(employee_id)
    #         res = leaves_bal[leave_type_id.id]['remaining_leaves']
    #     else:
    #         res = 0
    #     return res

    @api.multi
    def _get_leave_remaining_balance(self, holidays_status_rec, employee_id):
        """
        :return:
        """
        if holidays_status_rec and employee_id:
            leave_balance = \
                self.env['hr.holidays'].check_for_preliminary_leave(
                    holidays_status_rec, employee_id)
            return leave_balance

    @api.model
    def get_latest_policy(self, policy_group, dToday):
        '''Return an accrual policy with an effective date before dToday
        but greater than all the others'''
        if not policy_group or not policy_group.accr_policy_ids or not dToday:
            return None

        res = False
        for policy in policy_group.accr_policy_ids:
            dPolicy = datetime.strptime(policy.date, OE_DATEFORMAT).date()
            if dPolicy <= dToday:
                if not res:
                    res = policy
                elif dPolicy > datetime.strptime(
                        res.date, OE_DATEFORMAT).date():
                    res = policy
        return res

    def _get_amount_for_allocate(self, line, dHire, dToday, srvc_months,
                                 month_last_day, employee):
        if line.frequency_on_hire_date:
            freq_week_day = dHire.weekday()
            freq_month_day = dHire.day
            freq_annual_month = dHire.month
            freq_annual_day = dHire.day
        else:
            freq_week_day = line.frequency_week_day
            freq_month_day = line.frequency_month_day
            freq_annual_month = line.frequency_annual_month
            freq_annual_day = line.frequency_annual_day

        premium_amount = 0

        freq_week_day = int(freq_week_day)
        freq_month_day = int(freq_month_day)
        freq_annual_month = int(freq_annual_month)
        freq_annual_day = int(freq_annual_day)

        if line.calculation_frequency == 'weekly':
            if dToday.weekday() != freq_week_day:
                return
            freq_amount = float(line.accrual_rate) / 52.0
            if line.accrual_rate_premium_minimum <= srvc_months:
                premium_amount = (max(0, srvc_months -
                                      line.accrual_rate_premium_minimum +
                                      line.accrual_rate_premium_milestone
                                      )
                                  ) // (
                                     line.accrual_rate_premium_milestone *
                                     line.accrual_rate_premium / 52.0)
        elif line.calculation_frequency == 'monthly':
            # When deciding to skip an employee account for actual month
            # lengths. If
            # the frequency date is 31 and this month only has 30 days, go
            # ahead and
            # do the accrual on the last day of the month (i.e. the 30th). For
            # February, on non-leap years execute accruals for the 29th on
            # the 28th.
            #
            if dToday.day == \
                    month_last_day[dToday.month] and freq_month_day > \
                    dToday.day:
                if dToday.month != 2:
                    freq_month_day = dToday.day
                elif dToday.month == 2 and dToday.day == 28 and \
                                (dToday + timedelta(days=+1)).day != 29:
                    freq_month_day = dToday.day

            if dToday.day != freq_month_day:
                return

            freq_amount = float(line.accrual_rate) / 12.0
            if line.accrual_rate_premium_minimum <= srvc_months:
                premium_amount = (max(
                    0, srvc_months - line.accrual_rate_premium_minimum +
                       line.accrual_rate_premium_milestone)) // \
                                 line.accrual_rate_premium_milestone * \
                                 line.accrual_rate_premium / 12.0
        else:  # annual frequency
            # On non-leap years execute Feb. 29 accruals on the 28th
            #
            if dToday.month == 2 and dToday.day == 28 and (
                        dToday + timedelta(days=+1)).day != 29 and \
                            freq_annual_day > dToday.day:
                freq_annual_day = dToday.day

            if dToday.month != freq_annual_month or dToday.day != \
                    freq_annual_day:
                return

            freq_amount = line.accrual_rate
            if line.accrual_rate_premium_minimum <= srvc_months:
                premium_amount = (max(
                    0, srvc_months - line.accrual_rate_premium_minimum +
                       line.accrual_rate_premium_milestone)) // \
                                 line.accrual_rate_premium_milestone * \
                                 line.accrual_rate_premium

        if line.accrual_rate_max == 0:
            amount = freq_amount + premium_amount
        else:
            amount = min(freq_amount + premium_amount, line.accrual_rate_max)

        # Deposit to the accrual account

        emp_leave_balance = self._get_leave_remaining_balance(
            line.accrual_id.holiday_status_id, employee)

        return emp_leave_balance, amount

    @api.multi
    def _calculate_and_deposit(self, line, employee, job_id, dToday=False):
        leave_obj = self.env['hr.holidays']
        accrual_line_obj = self.env['hr.accrual.line']
        month_last_day = {
            1: 31,
            2: 28,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }

        srvc_months, dHire = \
            employee.get_months_service_to_date()[employee.id]
        srvc_months = int(srvc_months)
        if not dToday:
            dToday = date.today()
        if line.type != 'calendar':
            return

        employed_days = 0
        dCount = dHire
        while dCount < dToday:
            employed_days += 1
            dCount += timedelta(days=+1)
        if line.minimum_employed_days > employed_days:
            return

        emp_leave_balance, amount = self._get_amount_for_allocate(line,
                                                                     dHire, dToday,
                                               srvc_months, month_last_day,
                                               employee)

        if emp_leave_balance >= line.accrual_rate_max_balance:
            return
        elif emp_leave_balance + amount > line.accrual_rate_max_balance and \
                        line.accrual_rate_max_balance > 0:
            amount = line.accrual_rate_max_balance - emp_leave_balance

        accrual_line = {
            'date': dToday.strftime(OE_DATEFORMAT),
            'accrual_id': line.accrual_id.id,
            'employee_id': employee.id,
            'amount': amount,
        }
        acr_id = accrual_line_obj.create(accrual_line)
        line.accrual_id.write({'line_ids': [(4, acr_id.id)]})

        # Add the leave and trigger validation workflow
        #
        leave_allocation = {
            'name': 'Calendar based accrual (' + line.name + ')',
            'type': 'add',
            'employee_id': employee.id,
            'number_of_days_temp': amount,
            'holiday_status_id': line.accrual_id.holiday_status_id.id,
            'from_accrual': True,
            'allocation_date': dToday.strftime(OE_DATEFORMAT),
        }
        holiday_id = leave_obj.create(leave_allocation)

        holiday_id.holidays_to_manager()

        # workflow.trg_validate(
        #     uid, 'hr.holidays', holiday_id, 'final_aproval', cr)

        # Add this accrual line and holiday request to the job for this policy
        # line
        #
        job_id.write({'accrual_line_ids': [(4, acr_id.id)],
                      'holiday_ids': [(4, holiday_id.id)]})

    @api.multi
    def _get_last_calculation_date(self, accrual_id):
        job_obj = self.env['hr.policy.line.accrual.job']
        job_ids = job_obj.search([('policy_line_id', '=', accrual_id)],
                                 order='name desc', limit=1)
        if len(job_ids) == 0:
            return None
        return datetime.strptime(job_ids.name, OE_DATEFORMAT).date()

    @api.model
    def try_calculate_accruals(self):
        pg_obj = self.env['hr.policy.group']
        job_obj = self.env['hr.policy.line.accrual.job']
        dToday = datetime.now().date()
        pg_ids = pg_obj.search([])
        for pg in pg_ids:
            accrual_policy = self.get_latest_policy(pg, dToday)
            # Search accrual policy(res = date <= today) res = (date >
            # res.date)
            if not accrual_policy:
                continue

            # Get the last time that an accrual job was run for each accrual
            # line in
            # the accrual policy. If there was no 'last time' assume this is
            # the first
            # time the job is being run and start it running from today.
            #
            line_jobs = {}
            for line in accrual_policy.line_ids:
                d = self._get_last_calculation_date(line.id)
                if not d:
                    line_jobs[line.id] = [dToday]
                else:
                    line_jobs[line.id] = []
                    while d < dToday:
                        d += timedelta(days=1)
                        line_jobs[line.id].append(d)
            # For each accrual line in this accrual policy do a run for each
            # day (beginning
            # from the last date for which it was run) until today for each
            # contract attached
            # to the policy group.
            #
            for line in accrual_policy.line_ids:
                for dJob in line_jobs[line.id]:
                    job_vals = {
                        'name': dJob.strftime(OE_DATEFORMAT),
                        'execution_time': datetime.now().strftime(
                            OE_DATETIMEFORMAT),
                        'policy_line_id': line.id,
                    }
                    # Create a Job for the accrual line
                    job_id = job_obj.create(job_vals)
                    employee_list = []
                    for contract in pg.contract_ids:
                        if contract.employee_id.id in employee_list or \
                                        contract.state in ['draft', 'done']:
                            continue
                        if contract.date_end and \
                                        datetime.strptime(
                                            contract.date_end,
                                            OE_DATEFORMAT).date() < dJob:
                            continue
                        self._calculate_and_deposit(line,
                                                    contract.employee_id,
                                                    job_id, dToday=dJob)
                        # An employee may have multiple valid contracts. Don't
                        # double-count.
                        employee_list.append(contract.employee_id.id)
        return True


class hr_policy_line(models.Model):
    _name = 'hr.policy.line.accrual'
    _description = 'Accrual Policy Line'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    policy_id = fields.Many2one('hr.policy.accrual', string='Accrual Policy')
    accrual_id = fields.Many2one('hr.accrual', string='Accrual Account')
    type = fields.Selection([('standard', 'Standard'),
                             ('calendar', 'Calendar')], string='Type',
                            default='calendar')
    balance_on_payslip = fields.Boolean(string='Display Balance on Pay Slip',
                                        help='The pay slip report must be '
                                             'modified to display this accrual'
                                             ' for this setting to have any '
                                             'effect.')
    calculation_frequency = fields.Selection([('weekly', 'Weekly'),
                                              ('monthly', 'Monthly'),
                                              ('annual', 'Annual')],
                                             string='Calculation Frequency')
    frequency_on_hire_date = fields.Boolean(string='Frequency '
                                                   'Based on Hire Date')
    frequency_week_day = fields.Selection([('0', 'Monday'), ('1', 'Tuesday'),
                                           ('2', 'Wednesday'),
                                           ('3', 'Thursday'), ('4', 'Friday'),
                                           ('5', 'Saturday'),
                                           ('6', 'Sunday')], string='Week Day')
    frequency_month_day = fields.Selection([('1', '1'), ('2', '2'),
                                            ('3', '3'), ('4', '4'),
                                            ('5', '5'), ('6', '6'),
                                            ('7', '7'), ('8', '8'),
                                            ('9', '9'), ('10', '10'),
                                            ('11', '11'), ('12', '12'),
                                            ('13', '13'), ('14', '14'),
                                            ('15', '15'), ('16', '16'),
                                            ('17', '17'), ('18', '18'),
                                            ('19', '19'), ('20', '20'),
                                            ('21', '21'), ('22', '22'),
                                            ('23', '23'), ('24', '24'),
                                            ('25', '25'), ('26', '26'),
                                            ('27', '27'), ('28', '28'),
                                            ('29', '29'), ('30', '30'),
                                            ('31', '31')],
                                           string='Day of Month')
    frequency_annual_month = fields.Selection([('1', 'January'),
                                               ('2', 'February'),
                                               ('3', 'March'),
                                               ('4', 'April'),
                                               ('5', 'May'),
                                               ('6', 'June'),
                                               ('7', 'July'),
                                               ('8', 'August'),
                                               ('9', 'September'),
                                               ('10', 'October'),
                                               ('11', 'November'),
                                               ('12', 'December')],
                                              string='Month')
    frequency_annual_day = fields.Selection([('1', '1'), ('2', '2'),
                                             ('3', '3'), ('4', '4'),
                                             ('5', '5'), ('6', '6'),
                                             ('7', '7'), ('8', '8'),
                                             ('9', '9'), ('10', '10'),
                                             ('11', '11'), ('12', '12'),
                                             ('13', '13'), ('14', '14'),
                                             ('15', '15'), ('16', '16'),
                                             ('17', '17'), ('18', '18'),
                                             ('19', '19'), ('20', '20'),
                                             ('21', '21'), ('22', '22'),
                                             ('23', '23'), ('24', '24'),
                                             ('25', '25'), ('26', '26'),
                                             ('27', '27'), ('28', '28'),
                                             ('29', '29'), ('30', '30'),
                                             ('31', '31')],
                                            string='Day of Month')
    minimum_employed_days = fields.Integer(string='Minimum Employed Days',
                                           default=0)
    accrual_rate = fields.Float(string='Accrual Rate', help='The rate, '
                                                            'in days, '
                                                            'accrued per '
                                                            'year.')
    accrual_rate_premium = fields.Float(string='Accrual Rate Premium',
                                        help='The additional amount of time '
                                             '(beyond the standard rate) '
                                             'accrued per Premium Milestone '
                                             'of service.')
    accrual_rate_premium_minimum = fields.Integer(string='Months of '
                                                         'Employment Before '
                                                         'Premium', default=12,
                                                  help="Minimum number of "
                                                       "months the employee "
                                                       "must be employed "
                                                       "before "
                                                       "the premium rate "
                                                       "will start to accrue.")
    accrual_rate_premium_milestone = fields.Integer(
        string='Accrual Premium Milestone',
        help="Number of milestone months after which the premium rate "
             "will be added.")
    accrual_rate_max = fields.Float(string='Maximum Accrual Rate',
                                    default=0.0,
                                    help='The maximum amount of time that may '
                                         'accrue per year. Zero means the '
                                         'amount '
                                         'may keep increasing indefinitely.')
    job_ids = fields.One2many('hr.policy.line.accrual.job',
                              'policy_line_id', string='Jobs')
    accrual_rate_max_balance = fields.Float(string='Maximum Balance')


class policy_group(models.Model):
    _name = 'hr.policy.group'
    _inherit = 'hr.policy.group'

    accr_policy_ids = fields.Many2many('hr.policy.accrual',
                                       'hr_policy_group_accr_rel',
                                       'group_id', 'accr_id',
                                       string='Accrual Policy')


class hr_holidays(models.Model):
    _name = 'hr.holidays'
    _inherit = 'hr.holidays'

    # @api.multi
    # def _do_accrual(self, today, holiday_status_id, employee_id, days):
    #     accrual_obj = self.env['hr.accrual']
    #     accrual_line_obj = self.env['hr.accrual.line']
    #
    #     accrual_ids = accrual_obj.search([
    #         ('holiday_status_id', '=', holiday_status_id)])
    #
    #     if len(accrual_ids) == 0:
    #         return
    #
    #     # Deposit to the accrual account
    #     #
    #     accrual_line = {
    #         'date': today,
    #         'accrual_id': accrual_ids[0].id,
    #         'employee_id': employee_id,
    #         'amount': days,
    #     }
    #     line_rec = accrual_line_obj.create(accrual_line)
    #     accrual_ids[0].line_ids = [(4, line_rec.id)]
    #
    # @api.multi
    # def holidays_validate(self):
    #     res = super(hr_holidays, self).holidays_validate()
    #
    #     today = datetime.now().strftime(OE_DATEFORMAT)
    #     for record in self:
    #         if record.holiday_type == 'employee' and record.type == 'add' \
    #                 and not record.from_accrual:
    #             self._do_accrual(today, record.holiday_status_id.id,
    #                              record.employee_id.id,
    #                              record.number_of_days_temp)
    #
    #         elif record.holiday_type == 'employee' and record.type == 'remove':
    #             self._do_accrual(today, record.holiday_status_id.id,
    #                              record.employee_id.id,
    #                              record.number_of_days_temp)
    #     return res
    #
    # @api.multi
    # def holidays_refuse(self):
    #     today = datetime.now().strftime(OE_DATEFORMAT)
    #     for record in self:
    #         if record.state not in ['validate', 'validate1']:
    #             continue
    #
    #         if record.holiday_type == 'employee' and record.type == 'add':
    #             self._do_accrual(today, record.holiday_status_id.id,
    #                              record.employee_id.id,
    #                              record.number_of_days_temp)
    #
    #         elif record.holiday_type == 'employee' and record.type == 'remove':
    #             self._do_accrual(today, record.holiday_status_id.id,
    #                              record.employee_id.id,
    #                              record.number_of_days_temp)
    #     return super(hr_holidays, self).holidays_refuse()
