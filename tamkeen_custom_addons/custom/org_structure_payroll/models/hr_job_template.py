from odoo import models, api, fields


class HrJobTemplate(models.Model):
    _inherit = 'hr.job.template'


    struct_id = fields.Many2one('hr.payroll.structure', string='Salary '
                                                               'Structure',
                                help='Pay Scale')
    grade_level_id = fields.Many2one('grade.level',
                                      string='Job Grade Weight', help='Pay Grade')
