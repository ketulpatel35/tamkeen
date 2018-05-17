from odoo import models, fields, api, _

class Project(models.Model):
    _inherit = 'project.project'

    project_code = fields.Char(string='Project Code',track_visibility='onchange')