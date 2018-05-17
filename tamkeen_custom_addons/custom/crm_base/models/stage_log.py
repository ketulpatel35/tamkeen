# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class StageLog(models.Model):
    _name = 'crm.stage.log'
    _description = 'Lead/Opp. Stages Log'

    lead_id = fields.Many2one('crm.lead', 'Lead/Opportunity')
    user_id = fields.Many2one('res.users', 'Responsible')
    stage_id = fields.Many2one('crm.stage', 'Stage')
    prev_stage_id = fields.Many2one('crm.stage', 'Previous Stage')
    lead_type = fields.Selection(
        [('lead', 'Lead'), ('opportunity', 'Opportunity')], 'Type')

