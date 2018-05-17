from odoo import models, api


class hr_attendance_report_xls(models.TransientModel):
    _inherit = 'hr.attendance.report.xls'

    @api.model
    def default_get(self, fields_list):
        res = super(hr_attendance_report_xls, self).default_get(fields_list)
        context = dict(self._context)
        department_obj = self.env['hr.department']
        domain = []
        if self._context and context.get('active_id') and context.get('ess'):
            employee_rec = self.env['hr.employee'].search([
                ('user_id', '=', context.get('active_id'))], limit=1)
            if employee_rec:
                domain = [('manager_id', '=', employee_rec.id)]
        if domain:
            departments = department_obj.search(domain)
            if departments:
                new_domain = []
                new_domain.append(('id', 'child_of', departments.ids))
                departments = department_obj.search(new_domain)
            res.update({'department_ids': departments.ids})
        return res
