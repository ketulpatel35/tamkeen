from odoo import models, fields, api


class ProjectType(models.Model):
    _name = 'project.type'

    name = fields.Char('Name')
    code = fields.Char('Code')


