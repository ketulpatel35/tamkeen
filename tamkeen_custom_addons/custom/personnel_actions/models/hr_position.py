from odoo import models, fields, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    @api.multi
    def button_assignment(self):
        self.ensure_one()
        context = dict(self._context)
        return {
            'name': 'Assignment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'personnel.actions',
            'target': 'current',
            'context': context,
            'domain': ['|', ('prior_position_id', 'in', self.ids),
                       ('new_position_id', 'in', self.ids)]
        }
