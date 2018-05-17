from odoo import models, fields, api, _
import time
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class AttendanceSummaryEmployee(models.TransientModel):
    _name = 'attendance.summary.employee'
    _description = 'HR Attendance Summary Report By Employee'

    date_from = fields.Date(string='From', default=lambda *a: time.strftime(
        '%Y-%m-01'))
    date_to = fields.Date(string='To')
    employee_id = fields.Many2one('hr.employee', string='Employee')

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
                raise ValidationError(_(
                    'Date from must be smaller than Date to'))
            if self.date_to > add_days_from_strf:
                self.date_to = add_days_from_strf

    @api.model
    def default_get(self, fields_list):
        res = super(AttendanceSummaryEmployee, self).default_get(fields_list)
        if self.env.uid:
            employee_rec = self.env['hr.employee'].search([('user_id', '=',
                                                            self.env.uid)],
                                                          limit=1)
            if employee_rec:
                res.update({'employee_id': employee_rec.id})
        return res

    @api.multi
    def print_report(self):
        context = dict(self._context)
        self.ensure_one()
        [data] = self.read()
        # data['emp'] = self.env.context.get('active_ids', [])
        # employees = self.env['hr.employee'].browse(data['emp'])
        # employees = self.env['hr.employee'].search([
        #     ('user_id', '=', self.env.uid)])
        # if len(employees) > 1:
        #     raise Warning(_('There are multiple Employee with same user. '
        #                     'Please contact to HR for more information'))
        # if len(employees) <= 0:
        #     raise Warning(_('There are no Employee with same user. '
        #                     'Please contact to HR for more information'))
        context.update({'active_id': self.employee_id.id})
        # data['emp'] = [self.employee_id]
        # data['id'] = [employees.id]
        datas = {
            'ids': [],
            'model': 'hr.employee',
            'form': data
        }
        return self.env['report'].with_context(context).get_action(
            self.employee_id,
            'hr_attendance_employee_summary.report_attendancessummary',
            data=datas)


# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'
#
#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         args = args or []
#         domain = []
#         department_obj = self.env['hr.department']
#         context = dict(self._context) or {}
#         if context and context.get('filter_manager') and context.get('uid'):
#             employee_rec = self.search(
#                 [('user_id', '=', context.get('uid'))], limit=1)
#             if not self.user_has_groups(
#                     'hr_attendance.group_hr_attendance_user') and
# employee_rec:
#                 domain = [('manager_id', '=', employee_rec.id)]
#             if not employee_rec or not domain:
#                 if not self.user_has_groups(
#                         'hr_attendance.group_hr_attendance_user'):
#                     domain = [('id', 'in', ())]
#             departments = department_obj.search(domain, limit=limit)
#             if departments and domain:
#                 domain = [('name', operator, name), '|',
#                           ('manager_id', '=', employee_rec.id),
#                           ('id', 'child_of', departments.ids)]
#                 departments = department_obj.
# search(domain + args, limit=limit)
#             if departments:
#                 employee_rec += self.search(
#                     [('department_id', 'in', departments.ids)])
#                 employee_rec = self.browse(list(set(employee_rec.ids)))
#                 return employee_rec.name_get()
#         return super(HrEmployee, self).\
#             name_search(name, args=args, operator=operator, limit=limit)
