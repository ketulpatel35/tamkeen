from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

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
            'domain': [('employee_id', 'in', self.ids)]
        }
