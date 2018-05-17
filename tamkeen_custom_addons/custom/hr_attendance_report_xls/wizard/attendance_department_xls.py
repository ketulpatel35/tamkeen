from odoo import models, api, fields, _
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class hr_attendance_report_xls(models.TransientModel):
    _name = 'hr.attendance.report.xls'

    department_ids = fields.Many2many('hr.department',
                                      'department_report_xls_rel',
                                      'department_id', 'department_xls_id',
                                      string='Organization Unit')

    date_from = fields.Date(string='Date From',
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To')
    sign_in = fields.Boolean(string='Sign In', default=True)
    sign_out = fields.Boolean(string='Sign Out', default=True)
    working_hours = fields.Boolean(string='Working Hours', default=True)
    additional_hours = fields.Boolean(string='Additional Hours', default=True)
    permission_hours = fields.Boolean(string='Permission Hours', default=True)

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


class AttReportPringLink(models.Model):
    _name = 'att.report.print.link'

    xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Attendance_Report.xls')


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        context = dict(self._context) or {}
        current_employee = self.env['hr.employee'].search([
            ('user_id', '=', context.get('uid'))], limit=1)
        if context and context.get('is_report'):
            if not self.user_has_groups(
                    'hr_attendance.group_hr_attendance_user') and current_employee:
                domain = [('manager_id', '=', current_employee.id)]
            if not current_employee or not domain:
                if not self.user_has_groups(
                        'hr_attendance.group_hr_attendance_user'):
                    domain = [('id', 'in', ())]
        departments = self.search(domain, limit=limit)
        if departments and domain:
            domain = [('name', operator, name), '|',
                      ('manager_id', '=', current_employee.id),
                      ('id', 'child_of', departments.ids)]
        else:
            domain = [('name', operator, name)]
        departments = self.search(domain + args, limit=limit)
        return departments.name_get()
