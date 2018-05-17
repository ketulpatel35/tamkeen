from odoo import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    f_employee_no = fields.\
        Char(related='employee_id.f_employee_no',
             string='Employee Company ID', type='char')
