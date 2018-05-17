from odoo import fields, models, api, _


class ServiceLog(models.Model):
    _inherit = 'service.log'

    performance_appraisal_id = fields.Many2one('performance.appraisal',
                                       string='Appraisal Performance Request')


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
            if str(context.get('active_model')) == 'performance.appraisal':
                active_model_obj = self.env[context.get('active_model', False)]
                active_rec = active_model_obj.browse(context.get('active_id'))
                if context.get('calibration_by_vp'):
                    active_rec.with_context({
                        'reason': self.reason}).calibration_by_vp()
                    return service_log_rec
                service_log_rec.write({
                    'performance_appraisal_id': active_rec.id})
                if context.get('trigger') and context.get(
                        'trigger') == 'Returned':
                    active_rec.action_appraisal_performance_return()
                elif context.get('trigger') and context.get(
                        'trigger') == 'Reject':
                    active_rec.action_appraisal_performance_reject()
        return service_log_rec
