from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class service_panel_wizard(models.TransientModel):
    _name = 'service.panel.wizard'

    overtime = fields.Boolean(string='Overtime')
    pre_overtime = fields.Boolean(string='Pre Overtime')
    claim_overtime = fields.Boolean(string='Claim Overtime')

    @api.multi
    def open_service_panel(self):
        if self._context.get('default_model_id') and \
           self._context.get('default_is_model_found'):
            return {
                'name': 'Configure Service Panel States',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'service.panel.displayed.states',
                'target': 'current',
                'context': self._context
            }
        else:
            raise Warning(_('You can not start Service Panel'))


class ServiceLogWizard(models.TransientModel):
    _name = 'service.log.wizard'

    reason = fields.Text(string='Reason/Justification', required=1)

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.model
    def _create_service_log(self, vals):
        service_log_obj = self.env['service.log']
        service_log_rec = service_log_obj.create(vals)
        return service_log_rec

    @api.model
    def button_confirm(self):
        vals = {}
        context = dict(self._context)
        if context.get('active_model') and context.get('active_id'):
            active_model_obj = self.env[context.get('active_model', False)]
            active_id = context.get('active_id')
            active_rec = active_model_obj.browse(active_id)
            state_from = active_rec.state
            vals.update({'active_id': active_id,
                         'state_from': state_from})
            if context.get('trigger'):
                vals.update({'state_to': context.get('trigger')})
            if context.get('uid'):
                vals.update({'user_id': context.get('uid')})
            if self._get_current_datetime():
                vals.update(
                    {'activity_datetime': self._get_current_datetime()})
            if self.reason:
                vals.update(
                    {'reason': self.reason})
            service_log_rec = self._create_service_log(vals)
        return service_log_rec
