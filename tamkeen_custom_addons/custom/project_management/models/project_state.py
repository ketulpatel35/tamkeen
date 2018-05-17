from odoo import models, fields, api


class ProjectStage(models.Model):
    _name = 'project.stage'

    name = fields.Char('Name')
    code = fields.Char('Code')


