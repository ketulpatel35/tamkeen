from odoo import models, api, fields, _


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    employee_sub_group_id = fields.Many2one('hr.employee.group',
                                            string='Employee Sub Group')
    personnel_sub_area_id = fields.Many2one('personnel.area',
                                            string='Personnel Sub Area')


class HrJob(models.Model):
    _inherit = 'hr.job'

    maximum_allowed_annual_balance = fields.Float(string='Maximum Allowed '
                                                         'Annual Balance')
    maximum_accumulative_balance = fields.Float(
        string='Maximum Accumulative Balance')
    trial_period = fields.Float(
        string='Trial Period(Days)')

    @api.onchange('grade_level_id')
    def onchange_grade_level(self):
        if self.grade_level_id:
            self.maximum_allowed_annual_balance = \
                self.grade_level_id.maximum_allowed_annual_balance
            self.maximum_accumulative_balance = \
                self.grade_level_id.maximum_accumulative_balance
            self.trial_period = self.grade_level_id.trial_period