from odoo import api, fields, models, _
from datetime import date


class DashboardLine(models.Model):
    _name = "dashboard.line"
    _description = 'Dashboard'


    @api.multi
    def _compute_data(self):
        for rec in self:
            emp_rec = self.env['hr.employee'].search([('user_id', '=',
                                                       self._context.get('uid'))],
                                                     limit=1)
            schedule_hours = 0.0
            working_hours = 0.0
            shift_timeline_obj = self.env['shift.timeline']
            shift_rec = shift_timeline_obj._get_shift(emp_rec)
            if shift_rec:
                schedule_hours = shift_rec.default_scheduled_hours

            attendance_obj = self.env['hr.attendance']
            attendance_rec = attendance_obj.search([('date', '=', date.today()),
                                                    ('employee_id', '=',
                                                     emp_rec.id)])
            if attendance_rec:
                working_hours = str(attendance_rec.worked_hours)
            if emp_rec:
                rec.employee_id = emp_rec.id
                rec.emp_name = emp_rec.name
                rec.date = date.today()
                rec.schedule_hours = float(str(schedule_hours))
                rec.working_hours = float(str(working_hours))

    date = fields.Date(string='Date', index=True, compute=_compute_data)
    schedule_hours = fields.Float('Scheduled Hours')
    working_hours = fields.Float('Working Hours (Attendance, Onsite)')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    emp_name = fields.Char()


