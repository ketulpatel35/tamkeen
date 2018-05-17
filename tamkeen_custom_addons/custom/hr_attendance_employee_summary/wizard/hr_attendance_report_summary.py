from odoo import models, api, fields, _
import time
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
from odoo.report import report_sxw
from odoo.http import Controller, request, route


class hr_attendance_report_xls(models.TransientModel):
    _name = 'hr.attendance.report.pdf'

    department_ids = fields.Many2many('hr.department',
                                      'department_report_pdf_rel',
                                      'department_id', 'department_pdf_id',
                                      string='Organization Unit')

    date_from = fields.Date(string='Date From',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To')

    @api.onchange('date_from', 'date_to')
    def onchange_date_from(self):
        date_from_strp = datetime.strptime(self.date_from,
                                           DEFAULT_SERVER_DATE_FORMAT)
        add_days_from_strp = date_from_strp + relativedelta(days=30)
        add_days_from_strf = datetime.strftime(add_days_from_strp,
                                               DEFAULT_SERVER_DATE_FORMAT)
        next_month_date = date_from_strp + relativedelta(months=1, day=1)
        last_date = next_month_date - relativedelta(days=1)
        last_date_strf = datetime.strftime(last_date,
                                           DEFAULT_SERVER_DATE_FORMAT)
        if self.date_from and not self.date_to:
            self.date_to = last_date_strf

        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise \
                    Warning(
                        _('Date from must be earlier than Date to.'))
            if self.date_to > add_days_from_strf:
                self.date_to = add_days_from_strf


    @api.multi
    def print_pdf_report(self):
        context = dict(self._context)
        data = {
            'department_ids': self.department_ids.ids,
        }
        context.update({
            'dept':self.department_ids.ids,
            'date_from':self.date_from,
            'date_to':self.date_to,
        })
        return self.env['report'].with_context(context).get_action(
            self.id,'hr_attendance_employee_summary.report_attendance_new',
            data=data)

class Attendance_parcer(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(Attendance_parcer, self).__init__(cr, uid, name, context=context)
        self._cr, self._uid, self._context = cr, uid, context
        self.localcontext.update({
            '_get_employee_name': self._get_employee_name(),
            'get_header_info':self._get_header_info(),
            '_get_day': self._get_day,
            'get_months': self._get_months(),
            'get_data_from_report': self._get_data_from_report,
            'get_attendance_config': self._get_attendance_config(),

        })

    def _get_attendance_config(self):
        res = []
        for attendance in request.env['attendance.report.config'].search([]):
            res.append({
                'color_name': attendance.color_name,
                'name': attendance.name
            })
        return res

    def convert_in_time(self, hours):
        seconds = hours * 60 * 60
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return hours, minutes

    def get_public_holidays(self, year, employee):
        public_holidays_obj = request.env['hr.holidays.public']
        p_holidays_date = []
        p_holidays_line = public_holidays_obj.get_holidays_list(year, employee)
        for line in p_holidays_line:
            p_holidays_date.append(line.date)
        return p_holidays_date

    def _get_attendance_summary(self, start_date, end_date, employee_rec):
        res = []
        todays_date = datetime.now().date()
        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)
        month_days = (end_date - start_date).days + 1
        rest_days = self._get_rest_days(employee_rec)
        # rest_days = employee_rec.contract_id.working_hours.get_rest_days()
        total_worked_hours, total_permission_hours = 0.00, 0.00
        for index in range(0, month_days):

            current = start_date + timedelta(index)
            res.append({'day': current.day, 'color': '', 'worked_hours': '',
                        'check_in': '', 'check_out': '', 'permission_hours':
                            '', 'check_in_color': '', 'check_out_color': ''})
            attendance = request.env['hr.attendance']. \
                search([('employee_id', '=', employee_rec.id),
                        ('check_in', '<=', str(current)),
                        ('check_out', '>=', str(current)),
                        ('status', '!=', str('Duplicate'))], limit=1)
            # attendance = self.check_attendance(attendance_rec, current)
            holidays_rec = request.env['hr.holidays'] \
                .search([('employee_id', '=', employee_rec.id),
                         ('state', 'in', ('leave_approved',
                                          'validate')),
                         ('date_from', '<=', str(current)),
                         ('date_to', '>=', str(current)), ('type', '!=',
                                                           'add'
                                                           )],
                        limit=1)

            public_holidays_list = self.get_public_holidays(
                start_date.year, employee_rec.id)

            if current.weekday() in rest_days and not attendance:
                res[index]['check_in_color'] = '#ababab'
                res[index]['check_out_color'] = '#ababab'

            elif str(current) in public_holidays_list and not attendance:
                attendance_config_rec = \
                    request.env['attendance.report.config'].search([
                        ('public_holidays', '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name

            elif holidays_rec:
                attendance_config_rec = request.env[
                    'attendance.report.config'].search([('leave',
                                                         '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name

            elif current and employee_rec and attendance and attendance.status:
                check_in, check_out = self.get_check_in_out(attendance)
                # Check In Riyadh Timezone
                check_in_strp = datetime.strptime(
                    check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                check_in_riyadh = self.riyadh_timezone(check_in_strp)

                # Check Out Riyadh Timezone
                check_out_strp = datetime.strptime(
                    check_out, DEFAULT_SERVER_DATETIME_FORMAT)
                check_out_riyadh = self.riyadh_timezone(check_out_strp)

                if attendance.status == 'CORRECT' \
                        or attendance.status == 'Attendance Updated(Sign in)' \
                        or attendance.status == 'Attendance Updated(Sign out)':
                    res[index]['check_in'] = str(
                        datetime.strftime(check_in_riyadh, '%H:%M'))
                    res[index]['check_out'] = str(
                        datetime.strftime(check_out_riyadh, '%H:%M'))

                elif (attendance.status).strip() == 'NOT HAVE FIRST_IN':
                    attendance_config_rec = \
                        request.env['attendance.report.config'].search([
                            ('forget_check_in', '=', True)], limit=1)
                    res[index]['check_in_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_out'] = str(
                        datetime.strftime(check_out_riyadh, '%H:%M'))
                elif (attendance.status).strip() in \
                        ['LAST OUT before FIRST IN',
                         'FIRST_IN equal LAST OUT',
                         'Total is less than 2 minutes']:
                    attendance_config_rec = \
                        request.env['attendance.report.config'].search([
                            ('last_out_before_first_in', '=', True)], limit=1)
                    res[index]['check_in_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_out_color'] = \
                        attendance_config_rec.color_name

                elif (attendance.status).strip() == 'NOT HAVE LAST_OUT':
                    attendance_config_rec = \
                        request.env['attendance.report.config'].search([
                            ('forget_check_out', '=', True)], limit=1)
                    res[index]['check_out_color'] = \
                        attendance_config_rec.color_name
                    res[index]['check_in'] = str(
                        datetime.strftime(check_in_riyadh, '%H:%M'))

                if attendance.status and attendance.status \
                        not in ['LAST OUT before FIRST IN',
                                'FIRST_IN equal LAST OUT',
                                'Total is less than 2 minutes']:
                    w_hours, w_minutes = self.convert_in_time(
                        attendance.worked_hours)
                    worked_hours = "%02d:%02d" % (w_hours, w_minutes)
                    res[index]['worked_hours'] = worked_hours
                if attendance.status not in \
                        ['LAST OUT before FIRST IN',
                         'FIRST_IN equal LAST OUT',
                         'Total is less than 2 minutes']:
                    total_worked_hours += attendance.worked_hours

                if attendance.permission_hours and attendance.status:
                    p_hours, p_minutes = self.convert_in_time(
                        attendance.permission_hours)
                    permission_worked_hours = "%02d:%02d" % (p_hours,
                                                             p_minutes)
                    res[index]['permission_hours'] = \
                        permission_worked_hours
                    total_permission_hours += attendance.permission_hours
            elif current < todays_date:
                attendance_config_rec = request.env[
                    'attendance.report.config'].search([('absent',
                                                         '=', True)], limit=1)
                res[index][
                    'check_in_color'] = attendance_config_rec.color_name
                res[index][
                    'check_out_color'] = attendance_config_rec.color_name
        t_hours, t_minutes = self.convert_in_time(total_worked_hours)
        total_worked_hours_time = "%02d:%02d" % (t_hours, t_minutes)

        t_p_hours, t_p_minutes = self.convert_in_time(total_permission_hours)
        total_p_worked_hours_time = "%02d:%02d" % (t_p_hours, t_p_minutes)

        return {'res': res, 'total_worked_hours': total_worked_hours_time,
                'total_permission_hours': total_p_worked_hours_time}

    def _get_data_from_report(self, employee):
        res = [{'data': []}]
        employee_active_rec = employee
        if employee_active_rec:
            attendance_summary = self._get_attendance_summary(self._context.get('date_from'), self._context.get('date_to'), employee_active_rec)
            res[0]['data'].append({
                'emp': employee_active_rec.name,
                'display': attendance_summary.get('res'),
                'total_wh': attendance_summary.get('total_worked_hours'),
                'total_ph': attendance_summary.get('total_permission_hours'),
            })
        return res

    def _get_months(self):
        res = []
        start_date = fields.Date.from_string(self._context.get('date_from'))
        end_date = fields.Date.from_string(self._context.get('date_to'))
        while start_date <= end_date:
            last_date = start_date + relativedelta(day=1, months=+1, days=-1)
            if last_date > end_date:
                last_date = end_date
            month_days = (last_date - start_date).days + 1
            res.append({'month_name': start_date.strftime('%B'),
                        'days': month_days})
            start_date += relativedelta(day=1, months=+1)
        return res


    def _get_rest_days(self, employee):
        shift_timeline_obj = request.env['shift.timeline']
        rest_days = shift_timeline_obj._get_rest_days(employee)
        return rest_days

    def _get_day(self, employee):
        res = []
        context = self._context
        start_date = fields.Date.from_string(self._context.get('date_from'))
        end_date = fields.Date.from_string(self._context.get('date_to'))
        month_days = (end_date - start_date).days + 1
        if context:
            employee_active_id = employee
            rest_days = self._get_rest_days(employee_active_id)
            # rest_days = employee_rec.contract_id.working_hours.get_rest_days()
        for x in range(0, month_days):
            color = '#ababab' if start_date.weekday() in rest_days else ''
            # color = '#ababab' if start_date.strftime('%a') == 'Sat' or
            # start_date.strftime('%a') == 'Sun' else ''
            res.append({'day_str': start_date.strftime('%a'),
                        'day': start_date.day, 'color': color})
            start_date = start_date + relativedelta(days=1)
        return res

    def _get_header_info(self):
        start_date = self._context.get('date_from')
        end_date = self._context.get('date_to')
        st_date = fields.Date.from_string(start_date)
        en_date = fields.Date.from_string(end_date)
        return {
            'start_date': fields.Date.to_string(st_date),
            'end_date': fields.Date.to_string(en_date)
        }

    def _get_employee_name(self):
        emp_list = []
        departments = self._context.get('dept')
        employees = request.env['hr.employee'].search([('department_id','in',
                                                  departments)])
        if employees:
            for emp in employees:
                emp_list.append(emp)
        return emp_list

class report_custom_invoice_parser(models.AbstractModel):
    _name = 'report.hr_attendance_employee_summary.report_attendance_new'
    _inherit = 'report.abstract_report'
    _template = 'hr_attendance_employee_summary.report_attendance_new'
    _wrapped_report_class = Attendance_parcer


class hr_attendance_report_xls(models.TransientModel):
    _inherit = 'hr.attendance.report.xls'

    company_id = fields.Many2many('res.company', default=lambda self: self.env.user.company_id )
    @api.multi
    def print_pdf_report(self):
        context = dict(self._context)
        data = {
            'department_ids': self.department_ids.ids,
        }
        context.update({
            'dept': self.department_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        return self.env['report'].with_context(context).get_action(
            self.id, 'hr_attendance_employee_summary.report_attendance_new',
            data=data)