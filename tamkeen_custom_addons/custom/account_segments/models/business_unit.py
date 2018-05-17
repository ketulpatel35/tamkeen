# -*- coding: utf-8 -*-
from odoo import fields, models, api


# Cost centres
class BsCostCentre(models.Model):
    _name = 'bs.costcentre'
    _description = 'Cost Centre'
    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    department_id = fields.Many2one('bs.department', string="Department")
    note = fields.Text('Note')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        records = self.search(
            ['|', ('code', operator, name), ('name', operator, name)] + args,
            limit=limit)
        return records.name_get()

    @api.multi
    def name_get(self):
        """
        name should display with code
        :return:
        """
        res = []
        for record in self:
            code = record.code or ''
            name = record.name or ''
            display_name = '[ ' + code + ' ] ' + name
            res.append((record.id, display_name.title()))
        return res
