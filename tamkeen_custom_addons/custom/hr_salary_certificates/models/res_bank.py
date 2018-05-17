# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResBank(models.Model):
    _inherit = 'res.bank'


    arabic_name = fields.Char(string='Arabic Name')
