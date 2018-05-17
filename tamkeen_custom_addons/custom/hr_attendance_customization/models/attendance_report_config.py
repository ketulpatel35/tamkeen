from odoo import models, fields


class AttendanceReportConfig(models.Model):
    _name = 'attendance.report.config'

    name = fields.Char(string='Name')
    color_name = fields.Char(string='Color')
    active = fields.Boolean(string='Active', default=True)
    leave = fields.Boolean(string='Leave')
    public_holidays = fields.Boolean(string='Public Holidays')
    absent = fields.Boolean(string='Absent')
    forget_check_in = fields.Boolean(string='Forget Check In')
    forget_check_out = fields.Boolean(string='Forget Check Out')
    last_out_before_first_in = fields.Boolean(
        string='Wrong Finger-Print')


class HrAttendance(models.Model):
    _name = 'hr.attendance'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'hr.attendance']

    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now,
                               required=True, track_visibility='always')
    check_out = fields.Datetime(string="Check Out", track_visibility='always')
    sheet_id_computed = fields.Many2one('hr_timesheet_sheet.sheet',
                                        string='Compute Sheet',
                                        compute='_compute_sheet',
                                        index=True, ondelete='cascade',
                                        search='_search_sheet')
