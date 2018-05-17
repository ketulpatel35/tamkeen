# -*- encoding: utf-8 -*-
from odoo import fields, api, models


class PersonnelArea(models.Model):
    _name = 'personnel.area'
    _description = "Personeel Area"

    _sql_constraints = [
        ('code_uniq', 'unique(code, company_id)',
         'Code should be unique per Personnel Area!')]

    name = fields.Char('Name')
    code = fields.Char(string='Code')
    short_name = fields.Char('Short Name')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    parent_id = fields.Many2one('personnel.area', string='Personnel Area')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, index=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Company related to user.")
