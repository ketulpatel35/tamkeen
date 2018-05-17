from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT


class Project(models.Model):
    _inherit = 'project.project'

    @api.multi
    def _compute_attached_documents(self):
        for project in self:
            project.document_count = \
                self.env['project.documents'].search_count([
                    ('project_id', '=', project.id)])

    @api.depends('risks_ids')
    def _compute_risks_count(self):
        for project in self:
            project.risks_count = len(project.risks_ids)

    @api.multi
    def _check_end_date_data(self):
        for rec in self:
            if rec.date and rec.date_start and rec.date < rec.date_start:
                raise Warning(_('End date must be greater than the Start '
                                'date!'))

    @api.depends('avg_progress_percentage', 'date_start', 'date')
    def _calculate_spi(self):
        """
        to calculate spi
        :return: spi
        """
        for rec in self:
            rec._check_end_date_data()
            if rec.date_start and rec.date and rec.avg_progress_percentage:
                spi_data = 0.0
                current_progress = rec.avg_progress_percentage
                today = datetime.now().date()
                start_date = datetime.strptime(
                    rec.date_start, OE_DATEFORMAT).date()
                expected_end_date = datetime.strptime(
                    rec.date, OE_DATEFORMAT).date()
                diff1 = today - start_date
                diff2 = expected_end_date - start_date
                if diff1.days != 0 and diff2.days != 0:
                    diff_days = round(float(diff1.days) / float(diff2.days), 2)
                    if diff_days != 0:
                        spi_data = ((current_progress / 100) / float(
                            diff_days) / float(100) * float(100))
                    rec.spi = spi_data

    @api.depends('avg_progress_percentage')
    def calculate_avg_progress_percentage(self):
        for rec in self:
            total_milestones_percentage = 0.0
            rec.avg_progress_percentage = total_milestones_percentage

    @api.multi
    @api.depends('excepted_end_date')
    def _compute_days_of_delay(self):
        for rec in self:
            today = datetime.now().date()
            if rec.excepted_end_date:
                expected_end_date = datetime.strptime(
                    rec.excepted_end_date, OE_DATEFORMAT).date()
                days_del = today - expected_end_date
                rec.days_of_delay = days_del.days

    @api.constrains('avg_progress_percentage')
    def check_avg_progress_percentage(self):
        """
        :return:
        """
        for rec in self:
            if rec.avg_progress_percentage < 0 or \
                            rec.avg_progress_percentage > 100:
                raise ValidationError(_('Project Avg Progress Percentage '
                                        'should be in between 0 to 100 !'))


    revenue_stream_id = fields.Many2one('revenue.stream', 'Revenue Stream',
                                        copy=False, track_visibility='onchange')
    cost_center_id = fields.Many2one(
        'account.analytic.account', string='Cost Center',
        track_visibility='onchange',
        help='Select the cost center which will be affected by this request '
             'cost.', copy=False)
    business_unit_id = fields.Many2one(
        'hr.department', 'Business Unit', track_visibility='onchange')
    project_sponsor_id = fields.Many2one(
        'res.users', 'Project Sponsor', track_visibility='onchange')
    secondary_pm_id = fields.Many2one(
        'res.users', 'Secondary Project Manager', track_visibility='onchange')
    control_project_manager_id = fields.Many2one(
        'res.users', string='Control Project Manager', track_visibility='onchange')
    stakeholder_approval_date = fields.Date('Stakeholder Approval Date')
    avg_progress_percentage = fields.Monetary(
        'Avg Progress Percentage', compute=calculate_avg_progress_percentage,
        store=True)
    spi = fields.Float('SPI', compute=_calculate_spi, store=True)
    parent_project_id = fields.Many2one(
        'project.project', 'Parent Project', track_visibility='onchange')
    sub_project_ids = fields.One2many('project.project',
                                      'parent_project_id', 'Sub Project/s', track_visibility='onchange')
    project_type = fields.Many2one(
        'project.type', 'Project Type', track_visibility='onchange')
    project_stage = fields.Many2one(
        'project.stage', 'Project Stage', track_visibility='onchange')
    project_status = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('onhold', 'On-Hold'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('canceled', 'Canceled')],
        string='Project Status', required=True, default="new", track_visibility='onchange')
    rating_status = fields.Selection([
        ('stage', 'Rating when changing stage'),
        ('periodic', 'Periodical Rating'),
        ('on_coc_obtained', 'Rating when CoC obtained'), ('no', 'No rating')],
        help="How to get the customer's feedbacks?\n - Rating when changing "
             "stage: Email will be sent when a task/issue is pulled in "
             "another stage\n - Periodical Rating: Email will be sent "
             "periodically\n\n Don't forget to set up the mail templates on "
             "the stages for which you want to get the customer's feedbacks.",
        string='Customer(s) Ratings', required=True, default="no", track_visibility='onchange')
    # Purchase Order Details
    purchase_order = fields.Char('Purchase Order #')
    po_date_order = fields.Date('Purchase Order Date')
    po_amount_total = fields.Monetary('PO Value (SAR)')
    po_currency_id = fields.Many2one('res.currency',
                                     default=lambda self:
                                     self.env.user.company_id.currency_id, track_visibility='onchange')
    # Contract Details
    contract = fields.Char('Contract #')
    contract_signing_date = fields.Date(
        string='Contract Signing Date', default=fields.Datetime.now)
    contract_value = fields.Float('Contract Value (SAR)')
    contract_currency_id = fields.Many2one(
        'res.currency', string='Contract Currency',
        default=lambda self: self.env.user.company_id.currency_id, track_visibility='onchange')
    project_risks = fields.Boolean('Risks', default=True)
    have_parent_project = fields.Boolean('Have Parent Project ?', copy=False)
    risks_ids = fields.One2many('project.risks', 'project_id', 'Risks')
    risks_count = fields.Integer(
        compute='_compute_risks_count', string="Risks")
    privacy_visibility = fields.Selection([
        ('followers', _('On Invitation Only')),
        ('employees', _('Visible by All Employees')),
        ('portal', _('Visible by Following Customers')),
    ], string='Privacy', required=True, default='employees',
        help="Holds visibility of the tasks or issues that belong to the "
             "current project:\n"
             "- On invitation only: Employees may only see the followed "
             "project, tasks or issues\n"
             "- Visible by all employees: Employees may see all project, "
             "tasks or issues\n"
             "- Visible by following customers: employees see everything;\n"
             "   if website is activated, portal users may see project, "
             "tasks or issues followed by\n "
             "them or by someone of their company\n", track_visibility='onchange')
    document_count = fields.Integer(compute='_compute_attached_documents',
                                    string="Number of documents attached")
    date_start = fields.Date(string='Planned Start Date',
                             default=fields.Datetime.now,
                             index=True, copy=False)
    date = fields.Date(string='Planned End Date', index=True,
                       track_visibility='onchange')
    excepted_end_date = fields.Date('Expected End Date')
    actual_start_date = fields.Date('Actual Start Date')
    actual_end_date = fields.Date('Actual End Date')
    file_name_contract = fields.Char()
    contract_copy = fields.Binary(string='Contract Copy')
    code = fields.Char('Code')
    # deliverable_ids = fields.One2many('project.deliverable', 'project_id',
    #                                   string='Deliverables')
    days_of_delay = fields.Integer(string='Days of Delay',
                                   compute=_compute_days_of_delay, store=True)
    account_manager_id = fields.Many2one('res.users', string='Acccount '
                                                             'Manager', track_visibility='onchange')
    customer_ids = fields.One2many('res.partner', 'project_id',
                                   string='Customer Contacts', track_visibility='onchange')

    @api.onchange('partner_id')
    def onchange_partner_contact(self):
        for rec in self:
            rec.cost_center_id = False
            rec.customer_ids = False
            if rec.partner_id.child_ids:
                rec.customer_ids = [(6, 0, rec.partner_id.child_ids.ids)]
            cost_center_rec = self.env['account.analytic.account'].search([(
                'partner_id', '=',
                rec.partner_id.id)], limit=1)
            if cost_center_rec:
                rec.cost_center_id = cost_center_rec.id

    @api.model
    def default_get(self, fields_list):
        """
        set default value
        - allow_timesheets = false
        - privacy_visibility = followers
        :param fields_list:
        :return:
        """
        res = super(Project, self).default_get(fields_list)
        res.update({'allow_timesheets': False,
                    'privacy_visibility': 'followers'})
        return res

    @api.onchange('business_unit_id')
    def onchange_hr_department_buss_unit(self):
        """
        onchange business_unit(department) set project_sponsor
        :return:
        """
        if self.business_unit_id and self.business_unit_id.manager_id and \
                self.business_unit_id.manager_id.user_id:
            self.project_sponsor_id = \
                self.business_unit_id.manager_id.user_id.id

    @api.multi
    def get_risk_data(self):
        for rec in self:
            risk_rec = self.env['project.risks'].search([
                ('project_id', '=', rec.id)])
            if risk_rec:
                return risk_rec

    @api.multi
    def get_issue_data(self):
        for rec in self:
            issue_rec = self.env['project.issue'].search([
                ('project_id', '=', rec.id)])
            if issue_rec:
                return issue_rec

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return:
        """
        vals['code'] = self.env['ir.sequence'].next_by_code('project.seq')
        if vals.get('partner_id'):
            vals['customer_ids'] = [(6, 0, self.env['res.partner'].browse(
                vals.get('partner_id')).child_ids.ids)]
        project_id = super(Project, self).create(vals)
        project_task_type_ids = self.env['project.task.type'].search([('is_default_new_project','=',True)])
        for each_id in project_task_type_ids:
            each_id.write({'project_ids': [(6, 0, [project_id.id])]})
        return project_id

    @api.multi
    def write(self, vals):
        """
        :param vals:
        :return:
        """
        if vals.get('partner_id'):
            vals['customer_ids'] = [(6, 0, self.env['res.partner'].browse(
                vals.get('partner_id')).child_ids.ids)]
        # uid = self.env.user.id
        # for rec in self:
        #     if rec.user_id:
        #         if uid != rec.user_id.id:
        #             raise ValidationError(_('Only Primary Project Manager '
        #                                     'can Update Project Details!'))
        return super(Project, self).write(vals)

    @api.multi
    def unlink(self):
        for data in self:
            user_rec = self.env.user
            if not user_rec.has_group('project.group_project_manager'):
                raise ValidationError(
                    _('You are not allowed to delete a record'
                      ' '))
        return super(Project, self).unlink()

class Partner(models.Model):
    _inherit = 'res.partner'

    project_id = fields.Many2one('project.project', string='Project')
