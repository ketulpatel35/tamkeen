# -*- coding: utf-8 -*-
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class Stage(models.Model):
    _name = _inherit = 'crm.stage'

    state = fields.Char(string='Stage Code', unique=True)