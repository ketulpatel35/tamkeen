# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DestinationOrgPurpose(models.Model):
    _name = "destination.org.purpose"

    name = fields.Char('Name', copy=False)
    arabic_name = fields.Char('Arabic Name')
    description = fields.Char('Description', copy=False)
