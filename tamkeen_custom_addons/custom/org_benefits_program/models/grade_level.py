from odoo import api, fields, models, _


class grade_level(models.Model):
    _inherit = 'grade.level'

    education_flexible_one_budget = fields.Boolean(string='Education and'
                                                          'Flexible One '
                                                          'Budget')