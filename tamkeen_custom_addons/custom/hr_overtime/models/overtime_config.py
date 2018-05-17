from odoo import api, fields, models
from datetime import datetime


class OvertimeCalculationLine(models.Model):
    _name = 'overtime.calculation.line'
    _description = 'Overtime Calculation Line'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    type = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'),
                             ('rest_day', 'Rest Day'), ('public_holiday',
                                                        'Public Holiday')])
    rate = fields.Float(sring='Rate')
    active_from_time = fields.Char(string='Active From Time')
    active_to_time = fields.Char(string='Active To Time')
    service_configuration_panel_id = fields.Many2one(
        'service.configuration.panel', string='Service Configuration Panel')
    active_after = fields.Integer(string='Active After')
    weekly_working_days = fields.Integer(string='Weekly Working Days')
    maximum_hour = fields.Float(string='Maximum Hours')

    def _get_rest_days(self, employee):
        shift_timeline_obj = self.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    def _check_date_day_type(self, date, employee_rec):
        public_holidays_obj = self.env['hr.holidays.public']
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')
            public_holiday = public_holidays_obj.is_public_holiday(date)
            rest_days = self._get_rest_days(employee_rec)
            if public_holiday:
                date_day_type = 'public_holiday'
            elif date.weekday() in rest_days:
                date_day_type = 'rest_day'
            else:
                date_day_type = 'daily'
            return date_day_type

    def calculate_date_day_cost(self, date, expected_hours, policy_id,
                                employee_rec):
        date_day_type = self._check_date_day_type(date, employee_rec)
        day_cost = 0.0
        hourly_rate = employee_rec.contract_id.hourly_rate
        if date_day_type:
            for line in policy_id.overtime_calculation_line_ids:
                if line.type == date_day_type:
                    day_cost = line.rate * expected_hours * hourly_rate
        return day_cost

    def calculate_date_day(self, date, expected_hours, policy_id,
                                employee_rec):
        date_day_type = self._check_date_day_type(date, employee_rec)
        calculated_hours = 0.0
        if date_day_type:
            for line in policy_id.overtime_calculation_line_ids:
                if line.type == date_day_type:
                    calculated_hours = line.rate * expected_hours
        return calculated_hours


class OvertimeConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'Overtime Configuration Panel'

    @api.depends('model_id')
    def check_overtime(self):
        """
        check is overtime
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model in [
               'overtime.statement.request', 'overtime.pre.request']:
                rec.is_overtime = True

    maximum_hours_per_month = fields.Float(string='Maximum Hours Per Month')
    maximum_hours_per_year = fields.Float(string='Maximum Hours Per Year')
    overtime_salary_rule_input = fields.Many2one('hr.rule.input',
                                                 string='Overtime Salary '
                                                        'Rule Input')
    overtime_calculation_line_ids = fields.One2many(
        'overtime.calculation.line', 'service_configuration_panel_id',
        string='Overtime Calculation Line')
    overtime_pre_approval_type = fields.Selection([('required', 'Required'),
                                                   ('optional', 'Optional'),
                                                   ('not_available',
                                                    'Not Available')])
    pre_request_id = fields.Many2one('service.configuration.panel',
                                     string='Pre-Request ID')
    is_overtime = fields.Boolean('Is Overtime Policy',
                                 compute='check_overtime', store=True)
    hr_attendance_verification = fields.Boolean('Hr Attendance Verification')

    @api.onchange('overtime_pre_approval_type')
    def onchange_overtime_pre_approval_type(self):
        if self.overtime_pre_approval_type == 'not_available':
            self.pre_request_id = False


class ServiceLog(models.Model):
    _inherit = 'service.log'

    overtime_pre_request_id = fields.Many2one('overtime.pre.request',
                                              string='Overtime Pre Requests')
    overtime_claim_request_id = fields.Many2one(
        'overtime.statement.request', string='Overtime Claim Request')
