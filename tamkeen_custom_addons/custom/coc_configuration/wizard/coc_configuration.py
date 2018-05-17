from odoo import models, fields, api


class ServicePanelWizard(models.TransientModel):
    _inherit = 'service.panel.wizard'

    coc_confg = fields.Boolean(string='Certificate of Compeltion')

    @api.multi
    def open_service_panel(self):
        self.ensure_one()
        context = dict(self._context)
        ir_model_obj = self.env['ir.model']
        model_rec = False
        if self.coc_confg:
            model_rec = ir_model_obj.search([('model', '=',
                                              'certificate.of.completion')])
            if model_rec:
                context.update({'default_model_id': model_rec.id,
                                'default_is_model_found': True})
        return super(ServicePanelWizard,
                     self.with_context(context)).open_service_panel()
