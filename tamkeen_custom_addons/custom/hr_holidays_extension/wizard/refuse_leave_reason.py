from odoo import models, fields, api


class hr_refus_reason(models.TransientModel):
    _name = 'refuseleave.reason'

    @api.multi
    def refuseaction(self):
        context = dict(self._context) or {}
        if context.get('active_id'):
            holiday_rec = self.env['hr.holidays'].browse(
                context.get('active_id'))
            holiday_rec.get_approval_info()
            context.update({'reason': self.reason})
            if context.get('trigger') == 'refuse':
                holiday_rec.write({'refuse_reason': self.reason,
                                   'amend': True})
                holiday_rec.with_context(context).action_refuse()
            elif context.get('trigger') == 'cancel':
                holiday_rec.with_context(context).button_cancel()
            elif context.get('trigger') == 'return':
                holiday_rec.with_context(context).action_draft()
        return {'type': 'ir.actions.act_window_close'}

    reason = fields.Text(string='Justification')
