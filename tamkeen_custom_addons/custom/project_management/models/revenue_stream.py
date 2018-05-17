from odoo import models, fields, api


class RevenueStream(models.Model):
    _name = 'revenue.stream'

    name = fields.Char('Name')
    code = fields.Char('Code')
