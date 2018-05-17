from odoo import models, api, fields, _


class OrgBusinessTripRemoveWiz(models.TransientModel):
    _name = 'pa.objectives.locked.wizard'

    unlock = fields.Boolean('Unlock')

    @api.multi
    def action_pa_objectives_locked(self):
        context = dict(self._context) or {}
        if context.get('active_ids'):
            objectives_rec = self.env['pa.objectives'].browse(context.get(
                'active_ids'))
            for rec in objectives_rec:
                if self.unlock:
                    rec.locked_by_hr = False
                else:
                    rec.locked_by_hr = True