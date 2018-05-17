from odoo import models, fields, api


class HrGetEmployee_Wizard(models.TransientModel):
    _name = 'hr.get.employee.wizard'

    partner_ids = fields.Many2many('hr.employee',
                                   'hr_employee_details',
                                   'appraisal_id',
                                   'partner_id',
                                   string="Employees")

    @api.multi
    def generate_employee(self):
        context = self._context
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        appraisal_year_id = self.env[active_model].browse(active_id)
        if len(appraisal_year_id.emp_appraisal_line_ids) > 0:
            for rec in appraisal_year_id.emp_appraisal_line_ids:
                rec.unlink()
        emp_list = []
        for emp_rec in self.partner_ids:
            record = {
                'emp_id': emp_rec.id,
                'emp_no': emp_rec.id,
                'parent_id': emp_rec.parent_id.id,
                'upper_manager': emp_rec.parent_id.parent_id.id,
                'department_id': emp_rec.department_id.id,
                'job_id': emp_rec.job_id.id,
                'employee_role': emp_rec.employee_role,
                'manager': emp_rec.manager,
                'initial_employment_date': emp_rec.initial_employment_date,
                'state': 'pending',
            }
            emp_list.append((0, 0, record))
        appraisal_year_id.update({'emp_appraisal_line_ids': emp_list})
