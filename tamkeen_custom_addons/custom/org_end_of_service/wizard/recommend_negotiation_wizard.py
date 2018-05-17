from odoo import fields, models, api, _


class RecommendNegotiationWizard(models.TransientModel):
    _name = 'recommend.negotiation.wizard'

    is_recommend = fields.Boolean('I Recommend for Negotiation')
    reason = fields.Text('Reason')

    @api.multi
    def submit_button(self):
        """
        submit button
        :return:
        """
        if self._context.get('active_id') and self._context.get(
                'active_model') and self._context.get('state'):
            rec = self.env[self._context.get('active_model')].browse(
                self._context.get('active_id'))
            if rec:
                if self.is_recommend:
                    self.env['recommend.negotiation'].create({
                        'end_of_service_id': rec.id,
                        'reason': self.reason,
                    })
                if self._context.get('state') == 'mngr_approval':
                    return rec.action_submit_to_vp_approval()
                if self._context.get('state') == 'vp_approval':
                    return rec.action_submit_to_hr_approval()
        return False