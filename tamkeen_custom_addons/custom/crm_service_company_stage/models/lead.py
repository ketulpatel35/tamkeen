# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _name = _inherit = 'crm.lead'

    stage_state = fields.Char(string='Stage State', related='stage_id.state', store=True)

    def validate_stage_movement(self, lead_id, stage_id, next_stage_id):
        Stage = self.env['crm.stage']

        current_stage = Stage.browse(stage_id)
        next_stage = Stage.browse(next_stage_id)

        control = lead_id.team_id.stage_control_ids

        current_control = control.filtered(lambda r: r.stage_id.id == current_stage.id)
        if not current_control:
            return False
        nextt = False
        if next_stage.id in current_control.next_stage_ids.ids:
            nextt = True
            if current_control.disable_forward:

                return False

        if next_stage.id in current_control.back_stage_ids.ids:
            nextt = True
            if current_control.disable_backward:
                return False
                
        if not nextt:
            # next_stage_id not defined in allowed stages
            return False

        if self.env.user not in current_control.user_ids:
            return False
        
        return True


    def action_stage_changed(self, lead, old_stage_id, new_stage_id):
        Stage = self.env['crm.stage']
        super(Lead, self).action_stage_changed(lead, old_stage_id, new_stage_id)
        old_stage = Stage.browse(old_stage_id)
        new_stage = Stage.browse(new_stage_id)

        forward_backward = lead.forward_or_backward(old_stage, new_stage)[0]

        if forward_backward == -1:
            return

        forward = forward_backward == 1

        current_control = lead.team_id.stage_control_ids.filtered(lambda r: r.stage_id.id == new_stage.id)


        if forward:
            activities = current_control.next_activity_ids
        else:
            activities = current_control.back_activity_ids

        Action = self.env['crm.action']

        for activity in activities:
            action = {
                'partner_id': lead.partner_id.id,
                'reference_id': lead.reference_value,
                'user_id': lead.user_id.id,
                'action_type': activity.id,
                'details': activity.description,
                'date': fields.Date.context_today(self),
            }

            Action.create(action)


    @api.one
    def forward_or_backward(self, stage1, stage2):
        ''' check moving from stage1 to stage2 with stage control table, 
        and return if the stage1 is prev or next to stage2.
        returns 
            1 : if stage2 is next to stag1
            0 : if stage1 is next to stag2
            -1 : otherwise (no relations between the 2 stages)
        '''
        result = -1
        nextt, prevv = False, False
        current_control = self.team_id.stage_control_ids.filtered(lambda r: r.stage_id == stage1)

        if stage2.id in current_control.next_stage_ids.ids:
            nextt = True
            if current_control.disable_forward:
                nextt = False

        if stage2.id in current_control.back_stage_ids.ids:
            prevv = True
            if current_control.disable_backward:
                prevv = False

        if nextt:
            result = 1
        if prevv:
            result = 0

        return result
