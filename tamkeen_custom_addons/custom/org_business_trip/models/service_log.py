from odoo import fields, models, api, _


class ServiceLog(models.Model):
    _inherit = 'service.log'

    business_trip_id = fields.Many2one('org.business.trip',
                                       string='End of Service Request')


class ServiceLogWizard(models.TransientModel):
    _inherit = 'service.log.wizard'

    @api.multi
    def button_confirm(self):
        """
        Button Confirm
        :return:
        """
        context = dict(self._context)
        service_log_rec = super(ServiceLogWizard, self).button_confirm()
        if service_log_rec and context.get('active_id') and  context.get(
                'active_model'):
            if str(context.get('active_model')) == 'org.business.trip':
                active_model_obj = self.env[context.get('active_model', False)]
                active_rec = active_model_obj.browse(context.get('active_id'))
                service_log_rec.write({'business_trip_id': active_rec.id})
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.action_business_trip_return()
                elif context.get('trigger') and context.get(
                        'trigger') == 'Reject':
                    active_rec.action_business_trip_reject()
        return service_log_rec
