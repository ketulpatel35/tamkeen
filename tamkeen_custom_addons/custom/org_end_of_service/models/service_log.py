from odoo import fields, models, api, _


class ServiceLog(models.Model):
    _inherit = 'service.log'

    end_of_service_id = fields.Many2one('org.end.of.service',
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
            if str(context.get('active_model')) == 'org.end.of.service':
                active_model_obj = self.env[context.get('active_model', False)]
                active_rec = active_model_obj.browse(context.get('active_id'))
                service_log_rec.write({'end_of_service_id': active_rec.id})
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.action_end_of_service_return()
        return service_log_rec
