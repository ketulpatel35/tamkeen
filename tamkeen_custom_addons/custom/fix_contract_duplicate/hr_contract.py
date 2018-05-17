
from odoo import models, api


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def to_complate(self):
        for rec in self:
            rec.write({'state': 'close'})
        return True
