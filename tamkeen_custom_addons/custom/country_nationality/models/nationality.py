# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'

    nationality = fields.\
        Char(string='Nationality')
    name_eng = fields.Char(string='Arabic Name')
    continent = fields.Selection([
        ('asia', 'Asia'), ('africa', 'Africa'), ('europe', 'Europe'),
        ('australia', 'Australia'),('south_america', 'South America'),
        ('north_america', 'North America'), ('antarctica', 'Antarctica')],
        string='Continent')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.nationality:
                result.append((record.id, record.nationality))
            else:
                result.append((record.id, record.name))
        return result


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    _order = 'sequence'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Display Sequence')

    @api.multi
    def name_get(self):
        """
        state display name with country name
        :return:
        """
        result = []
        for record in self:
            name = record.name
            if record.country_id:
                name = record.name + ', ' + record.country_id.name
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        """
        search with state name and country name as well for all
        :param name:
        :param args:
        :param operator:
        :param limit:
        :return:
        """
        args = args or []
        records = self.search(
            ['|', ('country_id.name', operator, name),
             ('name', operator, name)] + args, limit=limit)
        return records.name_get()