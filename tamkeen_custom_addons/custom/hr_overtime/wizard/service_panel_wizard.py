from odoo import models, api


class Service_Panel_Wizard(models.TransientModel):
    _inherit = 'service.panel.wizard'

    @api.multi
    def open_service_panel(self):
        self.ensure_one()
        context = dict(self._context)
        ir_model_obj = self.env['ir.model']
        model_rec = False
        if self.overtime:
            if self.pre_overtime:
                model_rec = ir_model_obj.search([('model', '=',
                                                  'overtime.pre.request')])
            elif self.claim_overtime:
                model_rec = ir_model_obj.search([
                    ('model', '=', 'overtime.statement.request')])
        if model_rec:
            context.update({'default_model_id': model_rec.id,
                            'default_is_model_found': True})
        return super(Service_Panel_Wizard,
                     self.with_context(context)).open_service_panel()


class ServiceLogWizard(models.TransientModel):
    _inherit = 'service.log.wizard'

    @api.multi
    def button_confirm(self):
        context = dict(self._context)
        service_log_rec = super(ServiceLogWizard, self).button_confirm()
        if service_log_rec and context.get('active_id') and context.get(
                'active_model'):
            active_model_obj = self.env[context.get('active_model', False)]
            active_id = context.get('active_id')
            active_rec = active_model_obj.browse(active_id)
            if str(context.get('active_model')) \
                    == 'overtime.statement.request':
                service_log_rec.write(
                    {'overtime_claim_request_id': active_rec.id})
            if str(context.get('active_model')) == 'overtime.pre.request':
                service_log_rec.write(
                    {'overtime_pre_request_id': active_rec.id})
            if str(context.get('active_model')) == 'overtime.pre.request' or\
                    str(context.get('active_model')) == \
                    'overtime.statement.request':
                if context.get('trigger') and context.get('trigger') == \
                   'Rejected':
                    active_rec.with_context({'reason':
                                                 self.reason}).service_validate6()
                if context.get('trigger') and context.get('trigger') == \
                   'Locked':
                    active_rec.service_validate7()
                if context.get('trigger') and context.get('trigger') == \
                   'Closed':
                    active_rec.service_validate8()
                if context.get('trigger') and \
                        context.get('trigger') == 'Cancelled':
                    active_rec.service_validate9()
                if context.get('trigger') and context.get('trigger') == \
                   'Returned':
                    active_rec.service_validate10()
        return service_log_rec
