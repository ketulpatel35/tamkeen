from odoo import models, fields, api


class service_refus_reason(models.TransientModel):
    _name = 'refuseservice.reason'

    @api.multi
    def refuseaction(self):
        context = self._context or {}
        if context.get('active_id'):
            service_rec = self.env['service.request'].browse(
                context.get('active_id'))
            service_rec.refuse_reason = self.reason
            service_rec.action_refused()
        return {'type': 'ir.actions.act_window_close'}

    reason = fields.Text(string='Description')
