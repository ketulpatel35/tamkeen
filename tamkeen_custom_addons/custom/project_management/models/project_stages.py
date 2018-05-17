from odoo import models, fields, api, _


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    for_task = fields.Boolean('Stage for Task')
    for_issue = fields.Boolean('Stage for Issue')
    for_risk = fields.Boolean('Stage for Risk')
    for_document = fields.Boolean('Stage for Document')
    for_milestone = fields.Boolean('Stage for Milestone')
    is_default_new_project = fields.Boolean('Default for New Project')
