from odoo import api, fields, models, _
from odoo.exceptions import Warning

class Employee(models.Model):
    _inherit = 'hr.employee'

    grade_id = fields.Many2one(related='contract_id.grade_level',
                               string='Grade Level')