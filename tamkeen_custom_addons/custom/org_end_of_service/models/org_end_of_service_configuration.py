from odoo import fields, models, api, _
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT

SERVICE_STATUS_END_OF_SERVICE = [
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

    end_of_service_policy_id = fields.Many2one(
        'service.configuration.panel', string='End of Service Policy')


class EndOfServiceConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'
    _description = 'End of Service Configuration Panel'

    @api.depends('model_id')
    def check_end_of_service_policy(self):
        """
        check is end of service policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.end.of.service':
                rec.is_end_of_service = True

    is_end_of_service = fields.Boolean(
        string='End of Service Policy',
        compute='check_end_of_service_policy', store=True)
    eos_survey_id = fields.Many2one(
        'survey.survey', string='End of Service Interview Survey')

    @api.model
    def default_get(self, fields_list):
        res = super(EndOfServiceConfigurationPanel, self).default_get(fields_list)
        if self._context and self._context.get('end_of_service_model'):
            model_loan_rec = self.env['ir.model'].search([
                ('model', '=', 'org.end.of.service')], limit=1)
            res.update({'model_id': model_loan_rec.id})
        return res


class ServicePanelDisplayedStates(models.Model):
    _inherit = 'service.panel.displayed.states'

    wkf_state = fields.Selection(SERVICE_STATUS_END_OF_SERVICE,
                                 'Related State')

    @api.depends('model_id')
    def check_end_of_service_policy(self):
        """
        check is end of service policy
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == 'org.end.of.service':
                rec.is_end_of_service = True

    is_end_of_service = fields.Boolean(
        'is End of Service', compute='check_end_of_service_policy',
        store=True)

    @api.model
    def default_get(self, fields):
        res = super(ServicePanelDisplayedStates, self).default_get(fields)
        if self._context and self._context.get('end_of_service_model'):
            model_id = self.env['ir.model'].search([
                ('model', '=', 'org.end.of.service')])
            res.update({'model_id': model_id.id or False})
        return res
