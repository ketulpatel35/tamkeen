from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dep_eng_name = fields.Char(string='Arabic Name')
    vice_president_id = fields.Many2one('hr.employee', string="Vice President")
    ceo_id = fields.Many2one('hr.employee', string="CEO")
