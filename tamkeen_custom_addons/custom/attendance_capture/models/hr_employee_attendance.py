from odoo import models, fields, api


class HrEmployeeAttendance(models.Model):
    _inherit = 'hr.employee'

    attendance_identifier = fields.Char('Attendance ID')

    _sql_constraints = [('attendance_id_unique',
                         'UNIQUE(attendance_identifier)',
                         'Attendance Id Must be unique for per Employee!')]


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # @api.depends('worked_hours')
    @api.multi
    def _compute_worked_hours_in_time(self):
        for rec in self:
            result = '{0:02.0f}:{1:02.0f}'.\
                format(*divmod(rec.worked_hours * 60, 60))
            rec.worked_hours_time = result

    date = fields.Date('Date')
    total_hours = fields.Float('Total Hours')
    is_leave = fields.Boolean('is Leave')
    is_absent = fields.Boolean('is Absent')
    status = fields.Char('Status')
    f_employee_no = \
        fields.Char(related='employee_id.f_employee_no', string='Employee ID')
    worked_hours_time = fields.Char(string='Worked Hours(Time)',
                                    compute='_compute_worked_hours_in_time')

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        pass

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record
         compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        pass
