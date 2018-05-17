from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    timesheet_policy_id = fields.Many2one('service.configuration.panel',
                                     string='Timesheet Policy')


class ServiceLog(models.Model):
    _inherit = 'service.log'

    time_request_id = fields.Many2one('hr_timesheet_sheet.sheet',
                                      string='Timesheet Request')

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
            if str(context.get('active_model')) == 'hr_timesheet_sheet.sheet':
                service_log_rec.write({'time_request_id': active_rec.id})
            if str(context.get('active_model')) == 'hr_timesheet_sheet.sheet':
                if context.get('trigger') and context.get('trigger') == 'Rejected':
                    active_rec.with_context({'reason': self.reason}).timesheet_service_validate6()
                if context.get('trigger') and context.get('trigger') == 'Returned':
                    active_rec.with_context({'reason':
                                                 self.reason}).timesheet_service_validate7()
        return service_log_rec


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        model_id = self.env['ir.model'].search([('model', '=',
                                                 'hr_timesheet_sheet.sheet')])
        if self._context.get('timesheet_model'):
            res.update({
                'model_id': model_id.id or False})
        return res