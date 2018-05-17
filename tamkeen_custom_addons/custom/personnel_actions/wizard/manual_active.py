from odoo import models, api, fields, _
from odoo.exceptions import Warning


class ManualActive(models.TransientModel):
    _name = 'manual.active'

    @api.multi
    def manual_active(self):
        context = self._context or None
        not_approved_stage_warning = ''
        if context and context.get('active_ids'):
            personnel_action_rec = self.env['personnel.actions'].browse(
                context.get('active_ids'))
            for personnel_action in personnel_action_rec:
                if personnel_action.state != 'approved':
                    not_approved_stage_warning += str(
                        personnel_action.name) + ', '
                else:
                    personnel_action.button_active()
            if not_approved_stage_warning:
                raise Warning(_('To Proceed, These %s requests should be '
                                'in approved stage.')%
                              not_approved_stage_warning)