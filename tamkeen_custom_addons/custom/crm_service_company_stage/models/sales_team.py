# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class SalesTeam(models.Model):
    _name = _inherit = 'crm.team'

    stage_control_ids = fields.Many2many('crm.stage.control', 'team_stage_control_rel', string='Stages Control')
