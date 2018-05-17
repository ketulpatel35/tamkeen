# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProjectMilestonesSchedule(models.Model):
    _name = 'project.milestones.schedule'
    _description = 'Project Milestone Schedule'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'))
        return super(ProjectMilestonesSchedule, self).unlink()

    @api.depends('issue_ids')
    def _compute_issue_count(self):
        for rec in self:
            rec.issue_count = len(rec.issue_ids)

    @api.depends('task_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    @api.depends('risks_ids')
    def _compute_risks_count(self):
        for rec in self:
            rec.risks_count = len(rec.risks_ids)

    @api.depends('task_ids.task_completion_progress')
    def calculate_estimated_percentage(self):
        for rec in self:
            total_task_percentage = 0.0
            count = 0
            for taskrec in rec.task_ids:
                total_task_percentage += taskrec.task_completion_progress
                count += 1
            if total_task_percentage and count:
                rec.estimated_percentage = total_task_percentage / count

    def stage_find(self, section_id, domain=[], order='sequence'):
        """
        collect all section_ids
        :param section_id:
        :param domain:
        :param order:
        :return:
        """
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
        res = self.env['project.task.type'].search(search_domain, order=order,
                                                   limit=1).id
        # perform search, return the first found
        return res

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False),
                                            ('for_milestone', '=', True)])

    name = fields.Char('Milestone Name')
    project_id = fields.Many2one(
        'project.project', 'Project', track_visibility='onchange')
    po_order_line_id = fields.Many2one('purchase.order.line',
                                       string='Purchase Order Line', track_visibility='onchange')
    start_date = fields.Date(string='Start Date')
    due_date = fields.Date(string='Due Date')
    actual_completion_date = fields.Date(string='Actual Completion Date')
    is_coc_obtained = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                       string='CoC Obtained?', track_visibility='onchange')
    coc_justification = fields.Char(string='Justification')
    partner_id = fields.Many2one(
        'res.partner', string='Vendor', track_visibility='onchange')
    vendor_contract_value = fields.Float(string='Vendor Milestone Value (SAR)')
    purchase_order_no = fields.Char('Vendor PO#')
    estimated_percentage = fields.Float('Progress Completion(%)',
                                        compute='calculate_estimated_percentage',
                                        store=True)
    estimated_value = fields.Float('Contract Milestone Value (SAR)')
    risks_ids = fields.One2many('project.risks', 'milestones_schedule_id',
                                'Risks')
    task_ids = fields.One2many('project.task', 'milestones_schedule_id',
                               'Tasks')
    issue_ids = fields.One2many('project.issue', 'milestones_schedule_id',
                                'Tasks')
    stage_id = fields.Many2one(
        'project.task.type', string='Status', track_visibility='onchange',
        index=True, default=_get_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('project_ids', '=', project_id), ('for_milestone', '=', "
               "True)]", copy=False)
    sn_number = fields.Integer(string='Serial Number', default=1)
    task_count = fields.Integer(compute='_compute_task_count', string="Tasks")
    risks_count = fields.Integer(compute='_compute_risks_count',
                                 string="Risks")
    issue_count = fields.Integer(compute='_compute_issue_count',
                                 string="Issues")
    weightage = fields.Float(string="Weightage")
    code = fields.Char('Code')
    payment_involved = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                        string='Payment Involved ?', track_visibility='onchange')
    payment_invoiced = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                        string='Invoiced ?', track_visibility='onchange')
    invoiced_value = fields.Float(string='Invoiced Value', track_visibility='onchange')
    payment_collected = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                         string='Payment Collected ?', track_visibility='onchange')
    collected_payment = fields.Float('Collected Payment(SAR)')

    @api.constrains('start_date', 'due_date')
    def _check_end_date_data(self):
        for rec in self:
            if rec.due_date and rec.start_date and rec.due_date < \
                    rec.start_date:
                raise ValidationError(_('Due date must be greater than the '
                                        'Start date!'))

    @api.constrains('estimated_percentage')
    def check_percentage(self):
        """
        :return:
        """
        for rec in self:
            if rec.estimated_percentage < 0 or rec.estimated_percentage > 100:
                raise ValidationError(
                    _('Milestones Percentage should be in between '
                      '0 to 100 !'))

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'milestone.seq')
        return super(ProjectMilestonesSchedule, self).create(vals)
