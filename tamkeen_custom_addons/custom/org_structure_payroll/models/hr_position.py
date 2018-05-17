from odoo import models, api, fields


class HrJob(models.Model):
    _inherit = 'hr.job'


    struct_id = fields.Many2one('hr.payroll.structure', string='Salary '
                                                               'Structure',
                                help='Pay Scale')
    grade_level_id = fields.Many2one('grade.level', string='Grade Level',
                                      help='Pay Grade')

    @api.onchange('job_template_id')
    def onchange_job_template_id(self):
        super(HrJob, self).onchange_job_template_id()
        if self.job_template_id:
            self.struct_id = self.job_template_id.struct_id
            self.grade_level_id = self.job_template_id.grade_level_id