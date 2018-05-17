from odoo import fields, models, api, _

SERVICE_STATUS_BUSINESS_TRIP = [
    ('draft', 'To Submit'),
    ('mngr_approval', 'Manager Approval'),
    ('vp_approval', 'VP Approval'),
    ('hr_approval', 'HR Approval'),
    ('budget_approval', 'Budget Approval'),
    ('procurement_first_review', 'Procurement First Review'),
    ('business_owner_approval', 'Business Owner Approval'),
    ('procurement_second_review', 'Procurement Second Review'),
    ('pmo_approval', 'PMO Approval'),
    ('final_hr_approval', 'HR Review'),
    ('ceo_approval', 'CEO Approval'),
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

    business_trip_policy_id = fields.Many2one(
        'service.configuration.panel', string='Business Trip Policy')


class BusinessTripConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'Business Trip Configuration Panel'

    @api.depends('model_id')
    def check_business_trip_policy(self):
        """
        check is Business Trip policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.business.trip':
                rec.is_business_trip = True

    is_business_trip = fields.Boolean(
        string='Is Business Trip Policy',
        compute='check_business_trip_policy', store=True)
    display_internal_city_only = fields.Boolean(
        string='Display Internal City(s) only')
    business_trip_calculation_ids = fields.One2many(
        'business.trip.calculation', 'service_configuration_panel_id',
        string='Business Trip Calculation')

    @api.model
    def default_get(self, fields_list):
        res = super(BusinessTripConfigurationPanel, self).default_get(
            fields_list)
        if self._context and self._context.get('business_trip_model'):
            model_bt_rec = self.env['ir.model'].search([
                ('model', '=', 'org.business.trip')], limit=1)
            if model_bt_rec:
                res.update({'model_id': model_bt_rec.id})
        return res


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    wkf_state = fields.Selection(SERVICE_STATUS_BUSINESS_TRIP,
                                 'Related State')

    @api.depends('model_id')
    def check_business_trip_policy(self):
        """
        check is business trip policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.business.trip':
                rec.is_business_trip = True

    is_business_trip = fields.Boolean(
        string='Is Business Trip Policy',
        compute='check_business_trip_policy', store=True)

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        if self._context and self._context.get('business_trip_model'):
            model_id = self.env['ir.model'].search([
                ('model', '=', 'org.business.trip')])
            res.update({'model_id': model_id.id or False})
        return res


class BusinessTripCalculation(models.Model):
    _name = 'business.trip.calculation'
    _description = 'Business Trip calculation'

    name = fields.Char('Name')
    grade_level_ids = fields.Many2many(
        'grade.level', 'rel_grade_level_bt_conf', 'bt_id', 'grade_level_id',
        string='Grade Levels')
    # accommodation = fields.Float('Accommodation')
    # per_diem = fields.Float('Per Diem')
    bt_allowance_id = fields.Many2one(
        'business.trip.allowance', 'Business Trip Items')
    amount = fields.Float('Amount')
    bt_countries_group_id = fields.Many2one('bt.countries.group',
                                            'Countries Group')
    service_configuration_panel_id = fields.Many2one(
        'service.configuration.panel', 'Service Configuration Panel')


class BTCountriesGroup(models.Model):
    _name = 'bt.countries.group'
    _description = 'Business Trip Countries Group'

    name = fields.Char('Name')
    code = fields.Char('Code')
    maximum_allowed_travel_days = fields.Integer('Maximum Allowed Travel Days')
    country_ids = fields.One2many('res.country', 'bt_countries_group_id',
                                  'Country(s)')


class ServiceProofDocuments(models.Model):
    _inherit = 'service.proof.documents'

    @api.model
    def default_get(self, fields_list):
        res = super(ServiceProofDocuments, self).default_get(fields_list)
        if self._context and self._context.get('is_business_trip'):
            model_loan_rec = self.env['ir.model'].search([
                ('model', '=', 'org.business.trip')], limit=1)
            res.update({'model_id': model_loan_rec.id})
        return res


class BusinessTripProof(models.Model):
    _name = 'business.trip.proof'

    name = fields.Char(string='Name')
    description = fields.Text('Description')
    mandatory = fields.Boolean('Mandatory')
    document = fields.Binary('Document', attachment=True)
    document_file_name = fields.Char('File Name')
    business_trip_id = fields.Many2one('org.business.trip',
                                     string='Business Trip')
