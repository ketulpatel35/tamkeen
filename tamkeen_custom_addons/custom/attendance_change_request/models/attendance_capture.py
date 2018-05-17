from odoo import models, api
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT


class AttendanceCapture(models.Model):
    _inherit = 'attendance.capture.data'

    @api.multi
    def check_change_request(self, hr_attendance_rec):
        change_req_rec = self.env['attendance.change.request'].search([
            ('employee_id', '=', hr_attendance_rec.employee_id.id),
            ('state', '=', 'waiting_for_attendance'),
            ('attendance_id', '=', False),
            ('change_reason_id.code', '!=', 'working_in_different_location')
        ])
        if change_req_rec:
            for chnage_rec in change_req_rec:
                date = chnage_rec.date_from or chnage_rec.date_to
                change_req_date = datetime.strptime(date.split(' ')[0],
                                                    OE_DATEFORMAT).date()
                hr_att_date = datetime.strptime(
                    hr_attendance_rec.date.split(' ')[0], OE_DATEFORMAT).date()
                if hr_att_date == change_req_date:
                    change_req_rec.state = 'approved'
                    change_req_rec.attendance_change_approved(
                        hr_attendance_rec)
                    chnage_rec.attendance_id = hr_attendance_rec.id

    @api.model
    def _update_attendance(self):
        """
        read employee attendance Update in hr attendance object.
        mapping based on attendance_identifier field whitch is unique for
        per employee.
        :return:
        """
        exist_employee_list = []
        employee_obj = self.env['hr.employee']
        for att_capt_rec in self.search([('hr_attendance_id', '=', False)]):
            if not att_capt_rec.attendance_identifier:
                att_capt_rec.error = 'Attendence ID was not mapped !'
                continue
            # find employee based on Attendence ID
            emp_rec = employee_obj.search([
                ('attendance_identifier', '=',
                 att_capt_rec.attendance_identifier)])
            exist_employee_list.append(emp_rec.id)
            if not emp_rec:
                att_capt_rec.error = 'Employee not mapped with this ' \
                                     'Attendence ID !'
                continue
            if len(emp_rec) > 1:
                att_capt_rec.error = 'Multipe Employee find with this ' \
                                     'Attendence ID !'
                continue
            if emp_rec:
                first_in, last_out = self.get_first_in_last_out(att_capt_rec)
                total_hours = self.get_total_hours(att_capt_rec.total)
                if first_in and last_out:
                    hr_attendance_rec = self.create_attendance_record(
                        first_in, last_out, emp_rec, att_capt_rec, total_hours)
                    att_capt_rec.check_change_request(hr_attendance_rec)
                    att_capt_rec.write({
                        'hr_attendance_id': hr_attendance_rec.id,
                        'name': emp_rec.id,
                        'error': False,
                    })
