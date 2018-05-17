from odoo import fields, models, api, _

SERVICE_STATUS_PERFORMANCE_APPRAISAL = [
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

    performance_appraisal_policy_id = fields.Many2one(
        'service.configuration.panel', string='Appraisal Performance Policy')


class PerformanceAppraisalConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'Appraisal Performance Configuration Panel'

    @api.depends('model_id')
    def check_performance_appraisal_policy(self):
        """
        check is Appraisal Performance policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'performance.appraisal':
                rec.is_performance_appraisal = True

    is_performance_appraisal = fields.Boolean(
        string='Is Appraisal Performance Policy',
        compute='check_performance_appraisal_policy', store=True)
    performance_appraisal_type = fields.Selection([
        ('quarterly', 'Quarterly'), ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly')], 'Appraisal Performance Type')
    grade_level_ids = fields.Many2many(
        'grade.level', 'rel_grade_level_pa_conf', 'pa_conf_id',
        'grade_level_id', string='Grade Levels')
    is_use_objectives = fields.Boolean('Use Objectives')
    objectives_out_of_evaluation = fields.Float(
        'Objectives Out of Evaluation(%)')
    min_objectives = fields.Integer('Min. Objective per Appraisal')
    max_objectives = fields.Integer('Max. Objective per Appraisal')
    is_use_value = fields.Boolean('Use Value')
    value_out_of_evaluation = fields.Float('Value Out of Evaluation(%)')
    pa_value_ids = fields.Many2many(
        'pa.value', 'rel_pa_value_pa_conf', 'pa_conf_id', 'pa_value_id',
        'Value Items')
    is_use_personal_competencies = fields.Boolean('Use Personal Competencies')
    pc_out_of_evaluation = fields.Float(
        'Personal Competencies Out of Evaluation(%)')
    personal_competency_ids = fields.Many2many(
        'personal.competency', 'rel_pc_pa_conf', 'pa_conf_id', 'pc_id',
        'Personal Competency Items')

    @api.model
    def default_get(self, fields_list):
        res = super(PerformanceAppraisalConfigurationPanel, self).default_get(
            fields_list)
        if self._context and self._context.get('performance_appraisal_model'):
            model_pa_rec = self.env['ir.model'].search([
                ('model', '=', 'performance.appraisal')], limit=1)
            if model_pa_rec:
                res.update({'model_id': model_pa_rec.id})
        return res


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    wkf_state = fields.Selection(SERVICE_STATUS_PERFORMANCE_APPRAISAL,
                                 'Related State')

    @api.depends('model_id')
    def check_performance_appraisal_policy(self):
        """
        check is Appraisal Performance policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'performance.appraisal':
                rec.is_performance_appraisal = True

    is_performance_appraisal = fields.Boolean(
        string='Is Appraisal Performance Policy',
        compute='check_performance_appraisal_policy', store=True)

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        if self._context and self._context.get('performance_appraisal_model'):
            model_id = self.env['ir.model'].search([
                ('model', '=', 'performance.appraisal')])
            res.update({'model_id': model_id.id or False})
        return res
