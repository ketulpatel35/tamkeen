from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.exceptions import Warning, ValidationError


class ProjectRisks(models.Model):
    _name = 'project.risks'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'))
        return super(ProjectRisks, self).unlink()

    def stage_find(self, section_id, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('project_id').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('project_ids', '=', section_id))
        search_domain += list(domain)
        # perform search, return the first found
        return self.env['project.task.type'].search(search_domain,
                                                    order=order, limit=1).id

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False),
                                            ('for_risk', '=', True)])

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        # retrieve project_id from the context, add them to already fetched
        # columns (ids)
        if 'default_project_id' in self.env.context:
            search_domain = ['|', ('project_ids', '=', self.env.context[
                'default_project_id'])] + search_domain
        search_domain += [('for_risk', '=', True)]
        # perform search
        return stages.search(search_domain, order=order)

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

    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the project without removing it.")
    name = fields.Text('Risk Summary')
    project_id = fields.Many2one(
        'project.project', string='Project', track_visibility='onchange')
    business_unit_id = fields.Many2one('hr.department',
                                       related='project_id.business_unit_id',
                                       string='Business Unit', track_visibility='onchange')
    user_id = fields.Many2one('res.users',
                              related='project_id.user_id',
                              string='Primary Project Manager', track_visibility='onchange')
    project_sponsor_id = fields.Many2one(
        'res.users', related='project_id.project_sponsor_id',
        string='Project Sponsor', track_visibility='onchange')
    is_related_to_project_task = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')], default='no', track_visibility='onchange')
    project_task = fields.Many2one(
        'project.task', 'Project Task', track_visibility='onchange')
    cause = fields.Many2one('project.cause', 'Cause',
                            track_visibility='onchange')
    assigned_to = fields.Many2one(
        'res.users', 'Assigned To (Internal)', track_visibility='onchange')
    required_action = fields.Char('Action Required')
    due_date = fields.Date('Due Date')
    date_start = fields.Datetime(string='Starting Date',
                                 default=fields.Datetime.now,
                                 index=True, copy=False)
    excepted_closing_date = fields.Date('Expected Closing Date')
    excepted_end_date = fields.Date('Expected End Date')
    actual_end_date = fields.Date('Actual End Date')
    impact = fields.Selection([
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], track_visibility='onchange')
    priority = fields.Selection([('1','Lower'), ('2','Normal'),
                                 ('3', 'High')], index=True, track_visibility='onchange')
    severity = fields.Selection([('low','Low'), ('medium','Medium'),
                                 ('high', 'High')], track_visibility='onchange')
    sequence = fields.Integer(string='Sequence', index=True, default=10,
                              help="Gives the sequence order when displaying "
                                   "a list of Risks.")

    tag_ids = fields.Many2many(
        'project.tags', string='Tags', track_visibility='onchange')
    contact = fields.Many2one('res.partner', 'Contact',
                              track_visibility='onchange')
    email = fields.Char('Email')
    description = fields.Text('Description')
    stage_id = fields.Many2one(
        'project.task.type', string='Status', track_visibility='onchange',
        index=True, default=_get_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('project_ids', '=', project_id), ('for_risk', '=', True)]",
        copy=False)
    days_to_assign = fields.Float('Days to Assign')
    days_to_close = fields.Float('Days to Close')
    working_hours_to_assign_the_risk = fields.Float(
        'Working hours to Assign the Risk')
    working_hours_to_close_the_risk = fields.Float(
        'Working hours to Close the Risk')
    days_since_last_action = fields.Float('Days Since Last Action')
    progress = fields.Float('Progress(%)')
    color = fields.Integer(string='Color Index')
    code = fields.Char('Code')
    days_of_delay = fields.Integer(string='Days of Delay',
                                   compute=_compute_days_of_delay, store=True)
    main_assignment = fields.Selection([('internal', 'Internal'),
                                        ('external', 'External')],
                                       string='Main Assignment',
                                       default='internal', required=True, track_visibility='onchange')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')
    ], string='Kanban State',
        default='normal',
        track_visibility='onchange',
        required=True, copy=False,
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Normal is the default situation\n"
             " * Blocked indicates something is preventing the progress of this task\n"
             " * Ready for next stage indicates the task is ready to be pulled to the next stage")
    assigned_to_external = fields.Char('Assigned To (External)')

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'project.risk.seq')
        return super(ProjectRisks, self).create(vals)


class ProjectCause(models.Model):
    _name = 'project.cause'

    name = fields.Char('Name')
