from odoo import models, api, fields


class LevelIndexing(models.Model):
    _name = 'level.indexing'


    name = fields.Char(string='Name')
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code')
    sequence = fields.Integer(
        help='Used to order Indexing in the view', default=10)
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    active = fields.Boolean(string='Active', default=True)
    model_id = fields.Many2one('ir.model', string='Model')
