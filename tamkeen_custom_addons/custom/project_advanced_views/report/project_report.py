# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class ReportProjectRiskUser(models.Model):
    _name = "report.project.risk.user"
    _description = "Risks by user and project"
    _order = 'name desc, project_id'
    _auto = False

    name = fields.Char(string='Risk Title', readonly=True)
    user_id = fields.Many2one('res.users', string='Assigned To', readonly=True)
    date_start = fields.Datetime(string='Assignation Date', readonly=True)
    no_of_days = fields.Integer(string='# Working Days', readonly=True)
    date_end = fields.Datetime(string='Ending Date', readonly=True)
    due_date = fields.Date(string='Deadline', readonly=True)
    excepted_closing_date = fields.Datetime(string='Last Stage Update', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    closing_days = fields.Float(string='# Days to Close',
        digits=(16, 2), readonly=True, group_operator="avg",
        help="Number of Days to close the risk")
    opening_days = fields.Float(string='# Days to Assign',
        digits=(16, 2), readonly=True, group_operator="avg",
        help="Number of Days to Open the risk")
    delay_endings_days = fields.Float(string='# Days to Deadline', digits=(16, 2), readonly=True)
    nbr = fields.Integer('# of Risks', readonly=True)
    priority = fields.Selection([
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High')
        ], size=1, readonly=True)
    state = fields.Selection([
            ('normal', 'In Progress'),
            ('blocked', 'Blocked'),
            ('done', 'Ready for next stage')
        ], string='Kanban State', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Contact', readonly=True)
    stage_id = fields.Many2one('project.risk.type', string='Stage', readonly=True)

    def _select(self):
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.date_start as date_start,
                    t.due_date as date_end,
                    t.excepted_closing_date as excepted_closing_date,
                    t.due_date as due_date,
                    abs((extract('epoch' from (t.write_date-t.date_start)))/(3600*24))  as no_of_days,
                    assigned_to,
                    t.project_id,
                    t.priority,
                    t.name as name,
                    t.contact,
                    t.stage_id as stage_id,
                    t.kanban_state as state,
                    (extract('epoch' from (t.write_date-t.create_date)))/(3600*24)  as closing_days,
                    (extract('epoch' from (t.date_start-t.create_date)))/(3600*24)  as opening_days,
                    (extract('epoch' from (t.due_date-(now() at time zone 'UTC'))))/(3600*24)  as delay_endings_days
        """
        return select_str

    def _group_by(self):
        group_by_str = """
                GROUP BY
                    t.id,
                    create_date,
                    write_date,
                    date_start,
                    date_end,
                    due_date,
                    excepted_closing_date,
                    assigned_to,
                    t.project_id,
                    t.priority,
                    name,
                    t.contact,
                    stage_id
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE view %s as
              %s
              FROM project_risks t
                WHERE t.active = 'true'
                %s
        """ % (self._table, self._select(), self._group_by()))


class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"

    start_date = fields.Date('Start Date', readonly=True)
    excepted_end_date = fields.Date('Expected End Date', readonly=True)
    actual_end_date = fields.Date('Actual End Date', readonly=True)
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'),
                                 ('high', 'High')] , readonly=True)
    main_assignment = fields.Selection([('internal', 'Internal'),
                                        ('external', 'External')],
                                       string='Main Assignment',
                                       readonly=True)
    days_to_assign = fields.Float('Days to Start', readonly=True)
    days_to_close = fields.Float('Days to Close', readonly=True)
    task_completion_progress = fields.Float('Completion Progress(%)', group_operator='avg', readonly=True)
    code = fields.Char('Code', readonly=True)
    days_of_delay = fields.Integer(string='Days of Delay', readonly=True)
    date_deadline = fields.Date(string='Due Date', readonly=True)

    def _select(self):
        return super(ReportProjectTaskUser, self)._select() + """,
            t.start_date,
            t.excepted_end_date,
            t.actual_end_date,
            t.severity,
            t.main_assignment,
            t.days_to_assign,
            t.task_completion_progress,
            t.code,
            t.days_of_delay"""

    def _group_by(self):
        return super(ReportProjectTaskUser, self)._group_by() + """,
            t.start_date,
            t.excepted_end_date,
            t.actual_end_date,
            t.severity,
            t.main_assignment,
            t.days_to_assign,
            t.task_completion_progress,
            t.code,
            t.days_of_delay"""


class ProjectIssueReport(models.Model):
    _inherit = "project.issue.report"

    excepted_end_date = fields.Date('Expected End Date', readonly=True)
    actual_end_date = fields.Date('Actual End Date', readonly=True)
    severity = fields.Selection([('low', 'Low'), ('medium', 'Medium'),
                                 ('high', 'High')], readonly=True)
    code = fields.Char('Code', readonly=True)
    is_related_to_task = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Related To Task", readonly=True)
    days_of_delay = fields.Integer(string='Days of Delay', readonly=True)
    required_action = fields.Char('Action Required', readonly=True)
    main_assignment = fields.Selection([('internal', 'Internal'),
                                        ('external', 'External')],
                                       string='Main Assignment', readonly=True)
    assigned_to_external = fields.Char('Assigned To (External)', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'project_issue_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW project_issue_report AS (
                SELECT
                    c.id as id,
                    c.date_open as opening_date,
                    c.create_date as create_date,
                    c.date_last_stage_update as date_last_stage_update,
                    c.user_id,
                    c.working_hours_open,
                    c.working_hours_close,
                    c.stage_id,
                    c.date_closed as date_closed,
                    c.company_id as company_id,
                    c.priority as priority,
                    c.project_id as project_id,
                    1 as nbr_issues,
                    c.partner_id,
                    c.day_open as delay_open,
                    c.day_close as delay_close,
                    c.excepted_end_date,
                    c.actual_end_date,
                    c.severity,
                    c.is_related_to_task,
                    c.main_assignment,
                    c.required_action,
                    c.code,
                    c.assigned_to_external,
                    c.days_of_delay,
                    (SELECT count(id) FROM mail_message WHERE model='project.issue' AND message_type IN ('email', 'comment') AND res_id=c.id) AS email

                FROM
                    project_issue c
                LEFT JOIN project_task t on c.task_id = t.id
                WHERE c.active= 'true'
            )""")
