# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Proposal(models.Model):
    _name = _inherit = 'crm.proposal'

    effective_from = fields.Date(string='Effective From')
    effective_to = fields.Date(string='Effective To')
    delivery_date = fields.Date(string='Requested Delivery Date')
    due_date = fields.Date(string='Due Date')

    shipping_method_id = fields.Many2one('crm.shipping.method', string='Shipping Method')
    shipping_notes = fields.Html(string='Shipping Notes')

    shipping_address_id = fields.Many2one('res.partner', string='Ship To Address')
    ship_street = fields.Char(string='Street', related='shipping_address_id.street')
    ship_street2 = fields.Char(string='Street2', related='shipping_address_id.street2')
    ship_phone = fields.Char(string='Phone', related='shipping_address_id.phone')
    ship_fax = fields.Char(string='Fax', related='shipping_address_id.fax')
    ship_mobile = fields.Char(string='Mobile', related='shipping_address_id.mobile')
    ship_zip = fields.Char(string='Zip Code', related='shipping_address_id.zip')
    ship_city = fields.Char(string='City', related='shipping_address_id.city')
    ship_country_id = fields.Many2one('res.country', string='Country', related='shipping_address_id.country_id')
    ship_state_id = fields.Many2one('res.country.state', string='State / Region', related='shipping_address_id.state_id')

    billing_address_id = fields.Many2one(
        'res.partner', string='Bill To Address')
    bill_street = fields.Char(
        string='Street', related='billing_address_id.street')
    bill_street2 = fields.Char(
        string='Street2', related='billing_address_id.street2')
    bill_phone = fields.Char(
        string='Phone', related='billing_address_id.phone')
    bill_fax = fields.Char(string='Fax', related='billing_address_id.fax')
    bill_mobile = fields.Char(
        string='Mobile', related='billing_address_id.mobile')
    bill_zip = fields.Char(string='Zip Code', related='billing_address_id.zip')
    bill_city = fields.Char(string='City', related='billing_address_id.city')
    bill_country_id = fields.Many2one('res.country', string='Country', related='billing_address_id.country_id')
    bill_state_id = fields.Many2one('res.country.state', string='State / Region', related='billing_address_id.state_id')
