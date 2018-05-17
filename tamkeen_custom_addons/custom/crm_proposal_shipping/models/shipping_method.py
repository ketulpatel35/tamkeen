# -*- coding: utf-8 -*-
from openerp import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class ShippingMethod(models.Model):
    _name = 'crm.shipping.method'
    _order = 'order_sequence'
    _description = 'Proposal Shipping Method'

    name = fields.Char(string='Method Name')
    order_sequence = fields.Integer(string='Order Sequence', default=1)
    code = fields.Char(string='Code')
    sequence = fields.Char(string='Sequence')
    active = fields.Boolean(string='Active', default=True)