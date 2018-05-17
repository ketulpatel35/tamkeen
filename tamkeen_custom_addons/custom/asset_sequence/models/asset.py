# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models, api, tools


class AccountAssetAssetType(models.Model):
    _name = 'account.asset.asset.type'
    _description = 'Asset Type'

    name = fields.Char(string='Asset Type')


class AssetFields(models.Model):
    _inherit = 'account.asset.asset'

    barcode = fields.Char(string='Asset Barcode', track_visibility='onchange')
    type_id = fields.Many2one('account.asset.asset.type', string='Asset Type',
                              track_visibility='onchange')
    analytic_id = fields.Many2one('account.analytic.account',
                                  string='Analytic Account')
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  track_visibility='onchange')
    manufacturing_serial_number = fields.Char(
        string='Manufacturing Serial Number', track_visibility='onchange')
    asset_sequence_number = fields.Char('Asset Sequence', copy=False)

    @api.model
    def create(self, vals):
        if vals is None:
            vals = {}
        if not vals.get('asset_sequence_number', False):
            seq_num = self.env['ir.sequence'].next_by_code('asset.number.custom')
            vals['asset_sequence_number'] = seq_num
        return super(AssetFields, self).create(vals)
