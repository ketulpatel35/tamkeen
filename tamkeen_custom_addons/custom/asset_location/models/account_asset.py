from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class AccountAssetLocation(models.Model):
    _name = 'account.asset.location'

    name = fields.Char('Name')
    asset_ids = fields.One2many('account.asset.asset', 'location_id', 'Assets')
    default_location = fields.Boolean('Default')
    scrap_location = fields.Boolean('Scrap')

    @api.one
    @api.constrains('default_location', 'scrap_location')
    def check_locations(self):
        if self.default_location:
            default_location_ids = self.search([('default_location', '=', True),
                                                ('id', '!=', self.id)])
            if default_location_ids:
                raise ValidationError(_('You can have only one asset location as default!'))
        if self.scrap_location:
            scrap_location_ids = self.search([('scrap_location', '=', True),
                                              ('id', '!=', self.id)])
            if scrap_location_ids:
                raise ValidationError(_('You can have only one asset location as scrap!'))


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.model
    def _get_location(self):
        location_ids = self.env['account.asset.location'].search([('default_location', '=', True)])
        return location_ids and location_ids[0].id or False

    location_id = fields.Many2one('account.asset.location', 'Location', default=_get_location)

