# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.http import request
import datetime
from odoo.exceptions import Warning

class HrDashboard(models.Model):
    _name = 'hr.dashboard'
    _description = 'HR Dashboard'

    name = fields.Char("")

    @api.model
    def _check_group(self, group_xml_id_lst):
        user_rec = self.env.user
        for group_xml_id in group_xml_id_lst:
            if user_rec.has_group(str(group_xml_id)):
                return True
        return False

    @api.model
    def get_employee_info(self):
        """
        The function which is called from hr_dashboard.js.
        To fetch enough data from model hr and related dependencies.
        :payroll_dataset Total payroll generated according to months from
        model hr_payslip and hr_payslip_lines.
        :attendance_data Total worked hours and attendance details from
        models hr_attendace and hr_employee.
        :employee_table dict of datas from models hr_employee, hr_job,
        hr_department.
        :rtype dict
        :return: data
        """
        uid = request.session.uid
        cr = self.env.cr
        employee_id = self.env['hr.employee'].sudo().search_read(
            [('user_id', '=', uid)], limit=1)
        if not employee_id:
            raise Warning(_('Kindly, contact the HR team to link your user '
                            'with an employee profile.'))
        employee_team_members = self.env['hr.employee'].sudo().search_count(
            [('parent_id.user_id', '=', uid)])
        emp_team_contracts_count = self.env['hr.contract'].sudo().search_count(
            [('state','!=','close'), '|',
             ('employee_id.user_id.id', '=', uid),
             ('employee_id.parent_id.user_id.id', '=', uid)])
        leave_search_view_id = self.env.ref(
            'hr_holidays.view_hr_holidays_filter')
        job_search_view_id = self.env.ref(
            'hr_recruitment.view_crm_case_jobs_filter')
        attendance_search_view_id = self.env.ref(
            'hr_attendance.hr_attendance_view_filter')
        expense_search_view_id = self.env.ref(
            'hr_expense.view_hr_expense_sheet_filter')
        # leaves_alloc_to_approve = self.env['hr.holidays'].sudo(
        # ).search_count([('state', 'in', ['confirm', 'validate1']),
        # ('type', '=', 'add')])
        job_applications = self.env['hr.applicant'].sudo().search_count([])
        attendance_today = self.env['hr.attendance'].sudo().search_count(
            [('check_in', '>=',
              str(datetime.datetime.now().replace(hour=0, minute=0,
                                                  second=0))),
             ('check_in', '<=', str(
                 datetime.datetime.now().replace(hour=23, minute=59,
                                                 second=59)))])
        expenses_to_approve = self.env['hr.expense.sheet'].sudo().search_count(
            [('state', 'in', ['submit'])])
        # payroll Data's for Bar chart
        query = """
            select to_char(to_timestamp (date_part('month',
            p.date_from)::text, 'MM'), 'Month') as Month, sum(pl.amount) as
            Total from hr_payslip p INNER JOIN hr_payslip_line pl on
            (p.id = pl.slip_id and pl.code = 'NET' and p.state = 'done')
            group by month, p.date_from order by p.date_from
        """
        cr.execute(query)
        payroll_data = cr.dictfetchall()
        payroll_label = []
        payroll_dataset = []
        for data in payroll_data:
            payroll_label.append(data['month'])
            payroll_dataset.append(data['total'])
        # Attendance Chart Pie
        query = """
            select sum(a.worked_hours) as worked_hours, e.name_related as
            employee from hr_attendance a inner join hr_employee e on(
            a.employee_id = e.id) group by e.name_related
        """
        cr.execute(query)
        attendance_data = cr.dictfetchall()
        attendance_labels = []
        attendance_dataset = []
        for data in attendance_data:
            attendance_labels.append(data['employee'])
            attendance_dataset.append(data['worked_hours'])
        query = """
            select e.name_related as employee, e.barcode as badge_id, j.name
            as job, d.name as department, e.work_phone, e.work_email,
            e.work_location, e.gender, e.birthday, e.marital, e.passport_id,
            e.medic_exam, e.public_info from hr_employee e inner join hr_job
            j on (j.id = job_id) inner join hr_department d on (
            e.department_id = d.id)
        """
        cr.execute(query)
        employee_table = cr.dictfetchall()
        if employee_id:
            categories = self.env['hr.employee.category'].sudo().search(
                [('id', 'in', employee_id[0]['category_ids'])])
            data = {
                'categories': [c.name for c in categories],
                'leave_search_view_id': leave_search_view_id.id,
                'job_search_view_id': job_search_view_id.id,
                'employee_team_members': employee_team_members,
                'attendance_search_view_id': attendance_search_view_id.id,
                'expense_search_view_id': expense_search_view_id.id,
                'expenses_to_approve': expenses_to_approve,
                'job_applications': job_applications,
                'attendance_today': attendance_today,
                'payroll_label': payroll_label,
                'payroll_dataset': payroll_dataset,
                'attendance_labels': attendance_labels,
                'attendance_dataset': attendance_dataset,
                'emp_table': employee_table,
                'emp_team_contracts_count': emp_team_contracts_count,
            }
            employee_id[0].update(data)
        return employee_id
