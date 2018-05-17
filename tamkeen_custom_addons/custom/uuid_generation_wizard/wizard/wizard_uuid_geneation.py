from odoo import models, api, fields, _
import uuid


class UuidGenerationWizard(models.TransientModel):
    _name = 'uuid.wizard.generation'
    token = fields.Char(string='Token')

    @api.multi
    def generate_uuid(self):
        context = dict(self._context)
        for rec in self:
            view_uuid_wizard_generation = self.env.ref(
                'uuid_generation_wizard.view_uuid_wizard_generation', False)
            token = str(uuid.uuid4())
            context.update({'default_token': token})
            return {
              'name': _('Generate UUID'),
              'type': 'ir.actions.act_window',
              'view_type': 'form',
              'res_model': 'uuid.wizard.generation',
              'views': [(view_uuid_wizard_generation.id, 'form')],
              'view_id': view_uuid_wizard_generation.id,
              'target': 'new',
              'context': context
            }
