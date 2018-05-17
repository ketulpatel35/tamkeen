# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Technology(models.Model):
    _name = 'crm.technology'

    name = fields.Char(string='Technology Name', required=True)
    code = fields.Char(string='Code')
    short_name = fields.Char(string='Short Name')
    active = fields.Boolean(string='Active', default=True)
