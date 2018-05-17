from odoo import fields, models, api, _
# from odoo.exceptions import Warning


class RatingScale(models.Model):
    _name = 'rating.scale'
    _order = 'sequence'
    _description = 'Rating Scale'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Display Sequence')
    points = fields.Float('Points')
    description = fields.Text('Description')
