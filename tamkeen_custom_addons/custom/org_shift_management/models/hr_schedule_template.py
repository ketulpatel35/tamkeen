from odoo import models, api, fields, _


class HrScheduleTemplate(models.Model):
    _inherit = 'hr.schedule.template'

    code = fields.Char(string='Code')
    short_name = fields.Char(string='Short Name')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    employee_sub_group_id = fields.Many2one('hr.employee.group',
                                            string='Employee Sub Group')
    personnel_sub_area_id = fields.Many2one('personnel.area',
                                            string='Personnel Sub Area')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    # public_holiday_id = fields.Many2one('hr.holidays.public', string='Public Holidays')
    public_holiday_ids = fields.Many2many('hr.holidays.public',
                                          'hr_schedule_public_holidays_rel',
                                          'hr_schedule_id',
                                          'public_holiday_id',
                                          string='Public Holidays')
    default_scheduled_hours = fields.Char(string='Default Scheduled Hours')
    overnight_shift = fields.Boolean(string='Overnight Shift')
    # public_holiday_id = fields.Many2one('hr.holidays.public', string='Public Holidays')


class HrScheduleTemplateWorktime(models.Model):
    _inherit = 'hr.schedule.template.worktime'

    scheduled_hours = fields.Char(string='Scheduled Hours')
    flexible_hours = fields.Char(string='Flexible Hours')
    late_time = fields.Char(string='Late Time(M)')
    leave_early_time = fields.Char(string='Leave Early Time(M)')
    beginning_in = fields.Char(string='Beginning In')
    beginning_out = fields.Char(string='Beginning Out')
    ending_in = fields.Char(string='Ending In')
    ending_out = fields.Char(string='Ending Out')
