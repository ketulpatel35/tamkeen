# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class LeadSource(models.Model):
    _name = 'crm.lead.source'
    _order = 'order_sequence'
    _description = 'Lead / Opportunity Source'

    sequence = fields.Char(string='Sequence')
    code = fields.Char(string='Code')
    name = fields.Char(string='Source Name')
    order_sequence = fields.Integer(string='Order')
    active = fields.Boolean(string='Active', default=True)

class Lead(models.Model):
    _name = _inherit = 'crm.lead'

    name_arabic = fields.Char(string='Opportunity Name (Arabic)')
    sequence = fields.Char(string='Sequence')
    method = fields.Selection([
        ('in_person', 'In Person'),
        ('social_media', 'Social Media'),
        ('email', 'Email'),
    ], string='Method')
    reported_by = fields.Char(string='Reported By')
    project_type = fields.Selection([
        ('sub_contract', 'Sub contract'),
        ('vendor', 'Vendor'),
        ('company_services', 'Company Services'),
        ('profit_sharing', 'Profit Sharing'),
    ], string='Project Type')
    opportunity_analysis = fields.Text(string='Opportunity Analysis')
    estimated_budget = fields.Monetary(
        'Estimated Budget', currency_field='company_currency')
    delivery_model = fields.Selection(
        string='Delivery Model',
        selection=[
            ('by_company', _('By Company')),
            ('partner', _('Partner')),
            ('joint', _('Joint Work')),
        ],
    )

    selling_value = fields.Monetary(
        'Selling Value', currency_field='company_currency')
    confidence = fields.Integer(string='Confidence %')

    customer_situation = fields.Char(string='Customer Situation')
    customer_needs = fields.Char(string='Customer Needs')
    proposed_solution = fields.Char(string='Proposed Solution')
    lead_source_id = fields.Many2one('crm.lead.source', string='Lead Source')

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        Sequence = self.env['ir.sequence'].sudo()
        vals['sequence'] = Sequence.next_by_code('crm.lead')
        return super(Lead, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            for r in self:
                current_stage = r.stage_id.id
                new_stage = vals['stage_id']
                if not r.validate_stage_movement(r, current_stage, new_stage):
                    raise exceptions.AccessError(_('You dont have permission to move this Lead into next stage !'))
                wl = super(Lead, self).write(vals)
                r.log_stage_movement(
                    r, current_stage, new_stage)
                r.action_stage_changed(r, current_stage, new_stage)
                return wl
        return super(Lead, self).write(vals)

    def action_stage_changed(self, lead_id, stage_id, next_stage_id):
        ''' implemented by module extension '''
        pass
        
    def validate_stage_movement(self, lead_id, stage_id, next_stage_id):
        ''' implemented by module extension '''
        return True

    def log_stage_movement(self, lead_id, stage_id, next_stage_id):
        Log = self.env['crm.stage.log']
        data = {
            'lead_id': lead_id.id,
            'prev_stage_id': stage_id,
            'stage_id': next_stage_id,
            'lead_type': lead_id.type,
            'user_id': self.env.user.id,
        }
        Log.create(data)
