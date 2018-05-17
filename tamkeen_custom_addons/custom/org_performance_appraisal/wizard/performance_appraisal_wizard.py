from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class AppraisalPerformanceWizard(models.TransientModel):
    _name = 'appraisal.performance.wizard'

    name = fields.Char('Name')
    performance_appraisal_policy_id = fields.Many2one(
        'service.configuration.panel', string='Appraisal Performance Template')
    review_start_date = fields.Date('Review Start Date')
    review_end_date = fields.Date('Review End Date')
    due_start_date = fields.Date('Due Start Date')
    due_end_date = fields.Date('Due End Date')
    employee_ids = fields.Many2many(
        'hr.employee', 'rel_pa_emp_wiz', 'pa_wiz_id', 'emp_id', 'Employees')
    grade_level_ids = fields.Many2many(
        'grade.level', 'rel_gl_pa_wiz', 'pa_wiz_id', 'gl_id', 'Grade Levels')

    @api.onchange('performance_appraisal_policy_id')
    def onchange_performance_appraisal_policy_id(self):
        """
        :return:
        """
        domain = [('id', 'in', [])]
        grade_level_ids = []
        if self.performance_appraisal_policy_id:
            # display grade level
            grade_level_ids = \
                self.performance_appraisal_policy_id.grade_level_ids.ids
            # Employee Domain
            employee_ids = []
            grade_level_ids = \
                self.performance_appraisal_policy_id.grade_level_ids.ids
            for employee_rec in self.env['hr.employee'].search([]):
                if employee_rec.contract_id and \
                        employee_rec.contract_id.grade_level:
                    if employee_rec.contract_id.grade_level.id in \
                            grade_level_ids:
                        employee_ids.append(employee_rec.id)
            domain = [('id', 'in', employee_ids)]
        self.grade_level_ids = [(6, 0, grade_level_ids)]
        return {'domain': {'employee_ids': domain}}

    @api.multi
    def action_generate_appraisal(self):
        """
        :return:
        """
        for emp_rec in self.employee_ids:
            pa_rec = self.env['performance.appraisal'].create({
                'employee_id': emp_rec.id,
                'performance_appraisal_policy_id':
                    self.performance_appraisal_policy_id.id,
                'description': self.name,
                'review_start_date': self.review_start_date,
                'review_end_date': self.review_end_date,
                'due_start_date': self.due_start_date,
                'due_end_date': self.due_end_date
            })
            # call required onchange method for set values
            pa_rec.onchange_employee_id()
            pa_rec.onchange_performance_appraisal_policy_id()
            pa_rec.update_assessment()
