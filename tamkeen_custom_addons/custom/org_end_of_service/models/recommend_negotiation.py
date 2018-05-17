from odoo import fields, models, api, _


class RecommendNegotiation(models.Model):
    _name = 'recommend.negotiation'

    end_of_service_id = fields.Many2one('org.end.of.service', 'End of Service')
    user_id = fields.Many2one('res.users', string='Recommend By',
                              default=lambda self: self.env.user.id)
    date = fields.Datetime(default=fields.Datetime.now())
    reason = fields.Text('Reason')