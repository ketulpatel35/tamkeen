from odoo import fields, models


class GradeLevel(models.Model):
    _inherit = 'grade.level'

    policy_group_id = fields.Many2one('hr.policy.group', 'Policy Group')
