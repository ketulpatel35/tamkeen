# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _name = _inherit = 'crm.lead'

    technology_ids = fields.Many2many(
        'crm.technology', 'lead_technology_rel', string='Technology Stack')
