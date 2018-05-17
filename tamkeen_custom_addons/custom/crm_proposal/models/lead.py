# -*- coding: utf-8 -*-
from openerp import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.depends('proposal_ids.lead_id')
    def _compute_last_revision(self):
        for r in self:
            k = r.proposal_ids.sorted(key=lambda l: l.revision, reverse=True)
            if len(k):
                k = k[0]
            r.proposal_id = k
        
    document_type = fields.Selection([
        ('rfi', 'RFI'),
        ('rfp', 'RFP'),
        ('rfq', 'RFQ'),
    ], string='Bidding / Document Type', default='rfq')
    proposal_id = fields.Many2one('crm.proposal', string='Current Revision', compute='_compute_last_revision', store=True)
    proposal_ids = fields.One2many('crm.proposal', 'lead_id', string='Proposals')

    assignment_date = fields.Date(
        string='Assignment Date', related='proposal_id.assignment_date')
    planned_start_date = fields.Date(
        string='Planned Start Date', related='proposal_id.planned_start_date')
    proposal_writing_duration = fields.Float(
        string='Planned Proposal Writing Duration', related='proposal_id.proposal_writing_duration')
    planned_review_duration = fields.Float(
        string='Planned Review Duration', related='proposal_id.planned_review_duration')
    planned_release_date = fields.Date(string='Planned Release '
                                              'Date', related='proposal_id.planned_release_date')
    actual_start_date = fields.Date(
        string='Actual Start Date', related='proposal_id.actual_start_date')
    actual_release_date = fields.Date(
        string='Actual Release Date', related='proposal_id.actual_release_date')


    @api.multi
    def action_create_proposal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.proposal',
            'context': {
                'default_lead_id': self.id,
                'default_type': self.document_type,
                'default_partner_id': self.partner_id.id,
            },
        }
