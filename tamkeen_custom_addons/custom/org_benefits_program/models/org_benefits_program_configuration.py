from odoo import fields, models, api, _

SERVICE_STATUS_BENEFITS_PROGRAM = [
    ('draft', 'To Submit'),
    ('mngr_approval', 'Manager Approval'),
    ('vp_approval', 'VP Approval'),
    ('hr_approval', 'HR Approval'),
    ('budget_approval', 'Budget Approval'),
    ('procurement_first_review', 'Procurement First Review'),
    ('business_owner_approval', 'Business Owner Approval'),
    ('procurement_second_review', 'Procurement Second Review'),
    ('pmo_approval', 'PMO Approval'),
    ('ceo_approval', 'CEO Approval'),
    ('final_hr_approval', 'HR Review'),
    ('finance_processing', 'Finance Processing'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('open', 'Open'),
    ('locked', 'Locked'),
    ('closed', 'Closed'),
    ('cancelled', 'Cancelled'),
    ('payroll_processing', 'Payroll Processing'),
    ('waiting_repayment', 'Waiting Re-Payment')]


class ResCompany(models.Model):
    _inherit = 'res.company'

    benefits_program_policy_id = fields.Many2one(
        'service.configuration.panel', string='Benefits Program Policy')


class BenefitsProgramConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'Benefits Program Configuration Panel'

    @api.depends('model_id')
    def check_benefits_program_policy(self):
        """
        check is Benefits Program policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.benefits.program':
                rec.is_benefits_program = True

    is_benefits_program = fields.Boolean(
        string='Is Benefits Program Policy',
        compute='check_benefits_program_policy', store=True)
    is_display_dependents = fields.Boolean('Display Dependents')
    allow_maximum_dependents = fields.Integer('Maximum Dependents',
                                              default=3)
    allow_min_age = fields.Integer('allow Minimum Age', default=5)
    allow_max_age = fields.Integer('allow Maximum Age', default=18)
    is_display_sub_benefits = fields.Boolean('Display Sub-Benefits')
    bp_sub_benefits_ids = fields.Many2many(
        'bp.sub.benefits', 'rel_panel_sub_benefit', 'panel_id',
        'sub_benefit_id', 'Sub Benefits')
    bp_calculation_config_ids = fields.One2many(
        'bp.calculation.config', 'service_configuration_panel_id',
        string='Calculation')

    @api.onchange('is_display_dependents')
    def onchange_is_display_dependents(self):
        """
        :return:
        """
        if self.is_display_dependents:
            self.is_display_sub_benefits = False

    @api.onchange('is_display_sub_benefits')
    def onchange_is_display_sub_benefits(self):
        """
        :return:
        """
        if self.is_display_sub_benefits:
            self.is_display_dependents = False

    @api.model
    def default_get(self, fields_list):
        res = super(BenefitsProgramConfigurationPanel, self).default_get(
            fields_list)
        if self._context and self._context.get('benefits_program_model'):
            model_bp_rec = self.env['ir.model'].search([
                ('model', '=', 'org.benefits.program')], limit=1)
            if model_bp_rec:
                res.update({'model_id': model_bp_rec.id})
        return res


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    wkf_state = fields.Selection(SERVICE_STATUS_BENEFITS_PROGRAM,
                                 'Related State')

    @api.depends('model_id')
    def check_benefits_program_policy(self):
        """
        check is Benefits Program policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.benefits.program':
                rec.is_benefits_program = True

    is_benefits_program = fields.Boolean(
        string='Is Benefits Program Policy',
        compute='check_benefits_program_policy', store=True)

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        if self._context and self._context.get('benefits_program_model'):
            model_id = self.env['ir.model'].search([
                ('model', '=', 'org.benefits.program')])
            res.update({'model_id': model_id.id or False})
        return res


class SubBenefits(models.Model):
    _name = 'bp.sub.benefits'

    name = fields.Char('Name')
    code = fields.Char('Code')
    description = fields.Text('Description')


class BenefitsProgramCalculationConfig(models.Model):
    _name = 'bp.calculation.config'

    name = fields.Char('Name')
    grade_level_ids = fields.Many2many(
        'grade.level', 'rel_grade_level_bp_cal_conf', 'bt_id',
        'grade_level_id', string='Grade Levels')
    computation_rule = fields.Many2one('hr.salary.rule', 'Computation Rule')
    remarks = fields.Text('Remarks')
    service_configuration_panel_id = fields.Many2one(
        'service.configuration.panel', 'Service Configuration Panel')


class ServiceProofDocuments(models.Model):
    _inherit = 'service.proof.documents'

    @api.model
    def default_get(self, fields_list):
        res = super(ServiceProofDocuments, self).default_get(fields_list)
        if self._context and self._context.get('is_benefits_program'):
            model_loan_rec = self.env['ir.model'].search([
                ('model', '=', 'org.benefits.program')], limit=1)
            res.update({'model_id': model_loan_rec.id})
        return res


class BenefitsProof(models.Model):
    _name = 'benefits.proof'

    name = fields.Char(string='Name')
    description = fields.Text('Description')
    mandatory = fields.Boolean('Mandatory')
    document = fields.Binary('Document', attachment=True)
    document_file_name = fields.Char('File Name')
    benefits_program_id = fields.Many2one('org.benefits.program',
                                     string='Benefits Program')
