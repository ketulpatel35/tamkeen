from odoo import models, fields, api, _
from datetime import datetime,date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import Warning, ValidationError


class ProjectIssue(models.Model):

    _inherit = 'project.issue'

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'
                      ' '))
        return super(ProjectIssue, self).unlink()

    @api.constrains('progress')
    def check_avg_progress_percentage(self):
        """
        :return:
        """
        for rec in self:
            if rec.progress < 0 or rec.progress > 100:
                raise ValidationError(
                    _(' Progress Percentage should be in between '
                      '0 to 100 !'))

    @api.multi
    @api.depends('excepted_end_date')
    def _compute_days_of_delay(self):
        for rec in self:
            today = datetime.now().date()
            if rec.excepted_end_date:
                expected_end_date = datetime.strptime(rec.excepted_end_date,
                                                      OE_DATEFORMAT).date()
                days_del = today - expected_end_date
                rec.days_of_delay = days_del.days

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        res = super(ProjectIssue, self)._read_group_stage_ids(
            stages, domain, order)
        project_task_obj = self.env['project.task.type']
        for rec in res:
            if rec.for_issue:
                project_task_obj += rec
        return project_task_obj

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        res = super(ProjectIssue, self)._get_default_stage_id()
        if res:
            if self.env['project.task.type'].browse(res).for_issue:
                return res
        return False

    stage_id = fields.Many2one(
        'project.task.type', string='Status', track_visibility='onchange',
        index=True, default=_get_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('project_ids', '=', project_id), ('for_issue', '=', True)]",
        copy=False)
    excepted_end_date = fields.Date('Expected End Date')
    actual_end_date = fields.Date('Actual End Date')
    severity = fields.Selection([('low','Low'), ('medium','Medium'),
                                 ('high', 'High')], track_visibility='onchange')
    code = fields.Char('Code')
    is_related_to_task = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')], default='no')
    days_of_delay = fields.Integer(string='Days of Delay',
                                   compute=_compute_days_of_delay, store=True)
    required_action = fields.Char('Action Required')
    main_assignment = fields.Selection([('internal', 'Internal'),
                                        ('external', 'External')],
                                       string='Main Assignment',
                                       default='internal', required=True, track_visibility='onchange')
    assigned_to_external = fields.Char('Assigned To (External)')

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'project.issue.seq')
        return super(ProjectIssue, self).create(vals)
