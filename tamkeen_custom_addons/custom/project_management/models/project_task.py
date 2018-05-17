from odoo import models, fields, api, _
from datetime import datetime,date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DTFORMAT
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'
                      ' '))
        return super(ProjectTask, self).unlink()

    @api.constrains('start_date', 'date_deadline')
    def _deadline_date_check(self):
        for task in self:
            if task.start_date and task.date_deadline and task.date_deadline < task.start_date:
                raise ValidationError(_('Due date must be greater than the '
                                    'Start date!'))

    @api.depends('start_date')
    def _compute_days_to_assign(self):
        for rec in self:
            today = datetime.now().date()
            if rec.start_date:
                result = today - datetime.strptime(rec.start_date,
                                                   OE_DTFORMAT).date()
                rec.days_to_assign = result.days

    @api.depends('excepted_end_date')
    def _compute_days_to_close(self):
        for rec in self:
            today = datetime.now().date()
            if rec.excepted_end_date:
                result = datetime.strptime(rec.excepted_end_date,
                                           OE_DTFORMAT).date() - today
                rec.days_to_close = result.days

    @api.constrains('task_completion_progress')
    def check_avg_progress_percentage(self):
        """
        :return:
        """
        for rec in self:
            if rec.task_completion_progress < 0 or \
                            rec.task_completion_progress > 100:
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
                                                      OE_DTFORMAT).date()
                days_del = today - expected_end_date
                rec.days_of_delay = days_del.days

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        res = super(ProjectTask, self)._read_group_stage_ids(stages, domain,
                                                             order)
        project_task_obj = self.env['project.task.type']
        for rec in res:
            if rec.for_task:
                project_task_obj += rec
        return project_task_obj

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        res = super(ProjectTask, self)._get_default_stage_id()
        if res:
            if self.env['project.task.type'].browse(res).for_task:
                return res
        return False

    @api.onchange('project_id')
    def _onchange_project(self):
        if self.project_id:
            self.partner_id = self.project_id.partner_id
            self.stage_id = self.stage_find(self.project_id.id,
                                            [('fold', '=', False),
                                             ('for_task', '=', True)])
        else:
            self.stage_id = False

    stage_id = fields.Many2one(
        'project.task.type', string='Status', track_visibility='onchange',
        index=True, default=_get_default_stage_id,
        group_expand='_read_group_stage_ids', copy=False,
        domain="[('project_ids', '=', project_id), ('for_task', '=', True)]")
    start_date = fields.Date('Start Date')
    excepted_end_date = fields.Date('Expected End Date')
    actual_end_date = fields.Date('Actual End Date')
    severity = fields.Selection([('low','Low'), ('medium','Medium'),
                                 ('high', 'High')] ,track_visibility='onchange')
    main_assignment = fields.Selection([('internal','Internal'),
                                        ('external', 'External')],
                                       string='Main Assignment',
                                       default='internal', required=True, track_visibility='onchange')
    assigned_to_external = fields.Char('Assigned To (External)')
    # sequence = fields.Integer(string='Sequence', index=True, default=10,
    #                           help="Gives the sequence order when displaying"
    #                                "a list of Tasks.")
    days_to_assign = fields.Float(
        'Days to Start', compute='_compute_days_to_assign', store=True)
    days_to_close = fields.Float(
        'Days to Close', compute='_compute_days_to_close', store=True)
    working_hours_to_assign_the_task = fields.Float(
        'Working hours to Assign the Task')
    working_hours_to_close_the_task = fields.Float(
        'Working hours to Close the Task')
    days_since_last_action = fields.Float('Days Since Last Action')
    task_completion_progress = fields.Float('Completion Progress(%)')
    code = fields.Char('Code')
    days_of_delay = fields.Integer(string='Days of Delay',
                                   compute=_compute_days_of_delay, store=True)
    date_deadline = fields.Date(string='Due Date', index=True, copy=False)
    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['code'] = self.env['ir.sequence'].next_by_code('project.task.seq')
        return super(ProjectTask, self).create(vals)
