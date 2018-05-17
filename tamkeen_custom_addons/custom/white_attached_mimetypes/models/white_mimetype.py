from odoo import fields, models


class white_mimetype(models.Model):
    _name = 'white.mimetype'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active')

    _sql_constraints = [
        ('uniq_white_mimetype_name', 'UNIQUE(name)',
         'Name of mimetype must be unique !'),
    ]
