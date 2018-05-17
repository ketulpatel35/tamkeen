# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

SERVICE_STATUS_COC = [
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
    ('finance_processing', 'Finance Processing'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('open', 'Open'),
    ('done', 'Done'),
    ('locked', 'Locked'),
    ('closed', 'Closed'),
    ('cancelled', 'Cancelled'),
    ('payroll_processing', 'Payroll Processing'),
    ('waiting_repayment', 'Waiting Re-Payment')]


class ServiceConfigurationPanel(models.Model):
    _inherit = 'service.configuration.panel'

    @api.depends('model_id')
    def check_coc_policy(self):
        """
        check is coc
        :return:
        """
        for rec in self:
            if rec.model_id and rec.model_id.model == \
                    'certificate.of.completion':
                rec.is_coc = True

    is_coc = fields.Boolean('Is COC Policy',
                            compute='check_coc_policy', store=True)
    procurement_second_review = fields.Boolean('Procurement Second Review')
    business_owner_approval = fields.Boolean('Business Owner Approval')
    procurement_second_review_email = fields.Char(
        string='Procurement Second Review Email')
    pmo_approval = fields.Boolean('PMO Approval')
    pmo_approval_email = fields.Char('PMO Email')
    finance_processing = fields.Boolean('Finance Processing')
    finance_processing_email = fields.Char('Finance Processing Email')


class ServicePanelDisplayedStates(models.Model):
    _inherit = "service.panel.displayed.states"
    _description = 'Service Panel Displayed States'

    wkf_state = fields.Selection(SERVICE_STATUS_COC, 'Related State')

    @api.model
    def default_get(self, fields_list):
        res = super(ServicePanelDisplayedStates, self).default_get(fields_list)
        if self._context and self._context.get('coc_request'):
            model_coc_rec = self.env['ir.model'].search([
                ('model', '=', 'certificate.of.completion')], limit=1)
            res.update({'model_id': model_coc_rec.id})
        return res