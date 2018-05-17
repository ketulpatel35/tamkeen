# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class StageControl(models.Model):
    _name = 'crm.stage.control'
    _description = 'crm.stage.control'
    _order = 'order_sequence'

    name = fields.Char(string='Name')
    sequence = fields.Char(string='Sequence')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)

    stage_id = fields.Many2one('crm.stage', string='Stage')
    back_stage_ids = fields.Many2many(
        'crm.stage', 'stage_control_back_rel', string='Prev Stages')
    next_stage_ids = fields.Many2many(
        'crm.stage', 'stage_control_next_rel', string='Next Stages')

    user_ids = fields.Many2many(
        'res.users', 'users_stage_control_rel', string='Allowed Users')

    order_sequence = fields.Integer(string='Order Sequence', default=1)

    disable_backward = fields.Boolean(
        string='Disable Backward', help='''prevent moving Opportunity to the previuos stages''')
    disable_forward = fields.Boolean(
        string='Disable Forward', help='''prevent moving Opportunity to the next stages''')

    next_activity_ids = fields.Many2many('crm.activity', 'scontrol_next_activity_rel', string='Forward Activities', help='''recommended next stage activities''')
    back_activity_ids = fields.Many2many('crm.activity', 'scontrol_back_activity_rel', string='Backward Activities', help='''recommended backward activities''')
