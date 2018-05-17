# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.depends('milestones_schedule_id')
    def _compute_sub_task_count(self):
        for rec in self:
            rec.sub_task_count = self.search_count([('parent_task_id','=',rec.id)])

    parent_task_id = fields.Many2one('project.task', string="Parent Task")
    sub_task_count = fields.Integer(string="Sub Tasks", compute=_compute_sub_task_count)

    @api.constrains('start_date', 'date_deadline', 'excepted_end_date')
    def _deadline_date_check(self):
        for task in self:
            if task.start_date and task.date_deadline and task.date_deadline < task.start_date:
                raise ValidationError(_('Due date must be greater than the '
                                    'Start date!'))
            if task.parent_task_id:
                if task.start_date < task.parent_task_id.start_date:
                     raise ValidationError(_('Start date should be greater than '
                                             'Parent task Start date!'))
                if task.date_deadline > task.parent_task_id.date_deadline:
                     raise ValidationError(_('Due date should be less than '
                                             'Parent task due date!'))
                if task.excepted_end_date > task.parent_task_id.excepted_end_date:
                     raise ValidationError(_('Expected end date should be less than '
                                             'Parent task expected end date!'))

class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"

    parent_task_id = fields.Many2one('project.task', string="Parent Task")

    def _select(self):
        return super(ReportProjectTaskUser, self)._select() + """,
            t.parent_task_id"""

    def _group_by(self):
        return super(ReportProjectTaskUser, self)._group_by() + """,
            t.parent_task_id"""