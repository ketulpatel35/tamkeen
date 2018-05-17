# -*- encoding: utf-8 -*-
import logging

from odoo import models, fields, api, _


_logger = logging.getLogger(__name__)


class Activity(models.Model):
    _inherit = 'crm.activity'

    ref = fields.Char(string='Reference Code')
    active = fields.Boolean(string='Active', default=True)
    

class Action(models.Model):
    _name = 'crm.action'
    _description = 'CRM Action'
    _rec_name = 'ref'
    _order = 'date desc, ref'

    ref = fields.Char(string='Reference Code')

    def _get_supported_models(self):
        return [
            'crm.lead',
        ]

    def _get_reference_models(self):
        return [
            (m.model, m.name) for m in self.env['ir.model']\
                .search([('model', 'in', self._get_supported_models())])
        ]

    reference_id = fields.Reference(selection=_get_reference_models
        , string='Reference')

    @api.onchange('reference_id')
    def check_change(self):
        lead = self.reference_id
        if lead:
            self.update({
                'partner_id': lead.partner_id.id,
            })

    partner_id = fields.Many2one(
        'res.partner', string='Customer')

    date = fields.Date(
        'Date', required=True,
        default=fields.Date.context_today)

    user_id = fields.Many2one(
        'res.users', string='User', required=True,
        default=lambda self: self.env.user)

    def search_action_types(self):
        return self.env['crm.activity'].search(
            [('default', '=', True)])

    def default_action_type(self):
        action_types = self.search_action_types()
        return action_types and action_types[0].id or False

    action_type = fields.Many2one(
        'crm.activity', string='Type', required=True,
        default=default_action_type)

    details = fields.Text('Details')

    @api.onchange('action_type')
    def onchange_action_type(self):
        for r in self:
            r.update({
                'details': r.details or r.action_type.description,
            })

    state = fields.Selection(
        [
            ('todo', 'Todo'),
            ('done', 'Done'),
        ], string='Status', required=True,
        default="todo")

    @api.multi
    def button_confirm(self):
        self.write({'state': 'done'})

    @api.multi
    def button_set_to_draft(self):
        self.write({'state': 'draft'})

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        Sequence = self.env['ir.sequence'].sudo()
        if vals.get('action_type', False):
            at = vals.get('action_type', False)
            typ = self.env['crm.activity'].browse(at)
            seq = Sequence.next_by_code('crm.action')
            seq = u'{}{}'.format(typ.ref, seq)
            vals['ref'] = seq
        return super(Action, self).create(vals)
