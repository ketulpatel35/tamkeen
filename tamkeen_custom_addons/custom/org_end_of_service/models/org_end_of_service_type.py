from odoo import fields, models, api, _


class OrgEndOfServiceType(models.Model):
    _name = 'org.end.of.service.type'
    _description = 'End of Service Type'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
    description = fields.Text('Description')