from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def button_personnel_action(self):
        self.ensure_one()
        context = dict(self._context)
        return {
            'name': 'Personnel Actions',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'personnel.actions',
            'target': 'current',
            'context': context,
            'domain': [('contract_id', 'in', self.ids)]
        }