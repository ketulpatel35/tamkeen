from odoo import fields, models

ROLE = [('staff', 'Staff'),
        ('section_head', 'Section Head'),
        ('manager', 'Manager'),
        ('dep_manager', 'Department Manager'),
        ('director', 'Director'),
        ('vp', 'Vice President'),
        ('ceo', 'CEO'),
        ]


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    employee_role = fields.Selection(ROLE, string='Employee Role',
                                     default='staff')
