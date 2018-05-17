from odoo import api, models


class ServiceLogWizard(models.TransientModel):
    _inherit = 'service.log.wizard'

    @api.multi
    def button_confirm(self):
        context = dict(self._context)
        service_log_rec = super(ServiceLogWizard, self).button_confirm()
        if service_log_rec and context.get('active_id') and context.get(
                'active_model'):
            active_model = context.get('active_model')
            active_model_obj = self.env[active_model]
            active_id = context.get('active_id')
            active_rec = active_model_obj.browse(active_id)
            print context
            if str(active_model) == 'certificate.of.completion':
                service_log_rec.write(
                    {'coc_request_id': active_rec.id})
                # reject
                if context.get('trigger') and context.get(
                   'trigger') == 'Rejected':
                    active_rec.coc_service_validate6()
                # return
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.coc_service_validate10()
                # if context.get('trigger') and context.get(
                #    'trigger') == 'Locked':
                #     active_rec.service_validate7()
                # if context.get('trigger') and context.get(
                #    'trigger') == 'Closed':
                #     active_rec.service_validate8()
                # if context.get('trigger') and \
                #    context.get('trigger') == 'Cancelled':
                #     active_rec.coc_service_validate9()
        return service_log_rec