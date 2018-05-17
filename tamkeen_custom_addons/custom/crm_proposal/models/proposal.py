# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions
import odoo.addons.decimal_precision as dp

import logging


_logger = logging.getLogger(__name__)


class ProposalLine(models.Model):
    _name = 'crm.proposal.line'

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_price_total(self):
        for r in self:
            r.price_total = (r.product_uom_qty * r.price_unit) * \
                (1 - (r.discount or 0.0) / 100.0)
    
    sequence = fields.Integer(string='Sequence', default=1)
    name = fields.Char(string='Description')
    product_uom_qty = fields.Integer(string='Quantity', default=1)
    price_unit = fields.Monetary(string='Unit Price')
    discount = fields.Float(string='Discount (%)',
                            digits=dp.get_precision('Discount'), default=0.0)
    price_total = fields.Monetary(string='Line Total', compute='_compute_price_total')

    proposal_id = fields.Many2one('crm.proposal', string='Proposal')
    lead_id = fields.Many2one('crm.lead', string='Opportunity', ondelete='cascade')
    company_id = fields.Many2one(
        related='proposal_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(
        'res.currency', store=True, related='proposal_id.currency_id', string='Currency', readonly=True)

class Proposal(models.Model):
    _name = 'crm.proposal'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'CRM Proposal'
    _order ='revision desc, name desc, actual_start_date desc, assignment_date desc'
    _rec_name = 'display_name'


    @api.depends('revision')
    def _compute_revision(self):
        for r in self:
            r.revision_display = u'{}{}'.format('Revision #', r.revision)

    @api.depends('line_ids.product_uom_qty', 'line_ids.discount', 'line_ids.price_unit', 'discount')
    def _compute_total(self):
        for r in self:
            (
                total,
                total_discount,
                subtotal,
                lines_discount,
            ) = [0.0] * 4
            
            for l in r.line_ids:
                total += (l.product_uom_qty * l.price_unit) * \
                    (1 - (l.discount or 0.0) / 100.0)
                subtotal += (l.product_uom_qty * l.price_unit)
                lines_discount += (l.product_uom_qty * l.price_unit) * \
                    ((l.discount or 0.0) / 100.0)
            
            total -= r.discount
            total_discount += lines_discount + r.discount

            r.update({
                'total': total,
                'total_discount': total_discount,
                'subtotal': subtotal,
                'lines_discount': lines_discount,
            })

    @api.multi
    def button_dummy(self):
        return True

    @api.depends('name', 'revision_display')
    def _compute_display_name(self):
        for r in self:
            if not (r.name and r.revision_display):
                r.display_name = ''
            r.display_name = u'{} ({})'.format(r.name, r.revision_display)

    revision = fields.Integer(string='Revision Number', default=1)
    revision_display = fields.Char(string='Revision', compute='_compute_revision')
    parent_id = fields.Many2one('crm.proposal', string='Old Revision')
    child_id = fields.Many2one('crm.proposal', string='New Revision')
    assignment_date = fields.Date(string='Assignment Date')
    planned_start_date = fields.Date(string='Planned Start Date')
    proposal_writing_duration = fields.Float(
        string='Planned Proposal Writing Duration')
    planned_review_duration = fields.Float(string='Planned Review Duration')
    planned_release_date = fields.Date(string='Planned Release '
                                              'Date')
    actual_start_date = fields.Date(string='Actual Start Date')
    actual_release_date = fields.Date(string='Actual Release Date')
    state = fields.Selection([
        ('new', 'New'),
        ('writing', 'Writing'),
        ('submitted', 'Submitted'),
        ('re_submitted', 'Re-Submitted'),
        # new state (revised) mean the proposal 
        # is cloned with new revision
        # there's no need for the old state (re_submitted)
        ('revised', 'Revised'),
    ], default='new')
    lead_id = fields.Many2one('crm.lead', string='Opportunity')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id)

    name = fields.Char(string='Proposal Number')
    display_name = fields.Char(string='Proposal Number', compute='_compute_display_name', store=True)
    lead_sequence = fields.Char(string='Opportunity Sequence', related='lead_id.sequence', store=True)

    line_ids = fields.One2many('crm.proposal.line', 'proposal_id', string='Proposal Lines')

    discount = fields.Monetary(
        string='Subtotal Discount', currency_field='currency_id')

    total_discount = fields.Monetary(
        string='Total Discount', compute='_compute_total', currency_field='currency_id',
        help='''Discount on Subtotal + Discount on Items Lines''')
    lines_discount = fields.Monetary(
        string='Items Discount', compute='_compute_total', currency_field='currency_id',
        help='''Sum of discounts on Items Lines''')
    subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_total', currency_field='currency_id')
    total = fields.Monetary(
        string='Total', compute='_compute_total', currency_field='currency_id')

    
    selling_value = fields.Monetary(
        'Selling Value', related='lead_id.selling_value', currency_field='currency_id')
    partner_id = fields.Many2one('res.partner', string='Customer')

    currency_id = fields.Many2one(
        'res.currency', store=True, string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)

    type = fields.Selection([
        ('rfi', 'RFI'),
        ('rfp', 'RFP'),
        ('rfq', 'RFQ'),
    ], string='Bidding / Document Type', default='rfq')

    notes = fields.Text(string='Internal Notes')
    terms = fields.Text(string='Terms & Conditions')

    @api.multi
    def test_move_state(self):
        ''' TODO: remove this & its button '''
        for r in self:
            r.write({
                'state': 'writing',
            })

    @api.multi
    def action_create_revision(self):
        self.ensure_one()
        new = self.create_revision()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.proposal',
            'res_id': new.id,
        }

    @api.multi
    def action_open_revision(self):
        rev = self.env.context.get('revision', False)
        if not rev:
            return
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.proposal',
            'res_id': rev,
        }
    

    @api.multi
    def create_revision(self):
        self.ensure_one()
        required_fields = self._clone_revision_fields()
        required_fields['revision'] += 1
        new = self.create(required_fields)
        self._link_proposal_lines(new)
        self.write({
            'child_id': new.id,
            'state': 'revised',
        })
        new.write({
            'parent_id': self.id,
        })
        self._close_old_revision()
        self._after_clone_process(new)
        return new

    def _after_clone_process(self, new):
        ''' overwrite in inherited modules '''
        pass

    def _link_proposal_lines(self, new):
        required_fields = self._get_revision_line_fields_list()
        lines = self.line_ids.read(required_fields)
        updated = []
        m2o_fields = self._get_revision_line_m2o_fields_list()
        for l in lines:
            c = l.copy()
            for f in m2o_fields:
                c[f] = c[f] and c[f][0] or c[f]
            c['proposal_id'] = new.id
            updated.append(
                (0, 0, c),
            )
        new.write({
            'line_ids': updated,
        })

    def _get_revision_line_m2o_fields_list(self):
        return [
        ]

    def _get_revision_line_fields_list(self):
        FIELDS = [
            'sequence',
            'name',
            'price_unit',
            'product_uom_qty',
            'discount',
        ]
        return FIELDS

    def _get_revision_m2o_fields_list(self):
        return [
            'company_id',
            'partner_id',
            'currency_id',
            'lead_id',
        ]

    def _get_revision_fields_list(self):
        FIELDS = [
            'name',
            'revision',
            'discount',
            'assignment_date',
            'actual_release_date',
            'actual_start_date',
            'planned_release_date',
            'planned_start_date',
            'planned_review_duration',
            'proposal_writing_duration',
            'company_id',
            'lead_id',
            'type',
            'partner_id',
            'currency_id',
            'notes',
            'terms',
        ]
        return FIELDS

    def _clone_revision_fields(self):
        required_fields = self._get_revision_fields_list()
        rf = self.read(required_fields)[0]
        m2o_fields = self._get_revision_m2o_fields_list()
        for f in m2o_fields:
            rf[f] = rf[f] and rf[f][0] or rf[f]
        return rf

    def _close_old_revision(self):
        pass

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        ''' TODO: create sequence when workflow move from 'new' to 'writing' '''
        Sequence = self.env['ir.sequence'].sudo()
        if not vals.get('name', False):
            vals['name'] = Sequence.next_by_code('crm.proposal')
        return super(Proposal, self).create(vals)
