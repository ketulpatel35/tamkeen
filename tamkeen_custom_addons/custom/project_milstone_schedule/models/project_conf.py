from odoo import models, fields, api


class ProjectRisks(models.Model):
    _inherit = 'project.risks'

    milestones_schedule_id = fields.Many2one('project.milestones.schedule',
                                             string='Milestone Schedule', track_visibility='onchange')


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    milestones_schedule_id = fields.Many2one('project.milestones.schedule',
                                             string='Milestone Schedule', track_visibility='onchange')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    milestones_schedule_id = fields.Many2one('project.milestones.schedule',
                                             string='Milestone Schedule', track_visibility='onchange')
