# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.depends('action_ids')
    def _compute_count_actions(self):
        self.actions_count = len(self.action_ids)

    def _compute_acion_ids(self):
        Action = self.env['crm.action']
        for r in self:
            r.action_ids = Action.search([
                ('reference_id', '=', u'crm.lead,{}'.format(r.id))
            ])

    def _compute_reference_value(self):
        for r in self:
            r.reference_value = u'crm.lead,{}'.format(r.id)

    reference_value = fields.Char(compute='_compute_reference_value', store=True)
    actions_count = fields.Integer(compute='_compute_count_actions')
    action_ids = fields.Many2many(
        'crm.action', 'lead_action_rel', string='Actions', compute='_compute_acion_ids')

    @api.multi
    def button_actions(self):
        self.ensure_one()
        actions = self.env['crm.action'].search([
            ('reference_id', '=', u'crm.lead,{}'.format(self.id))
        ])
        res = {
            'name': _('Actions'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.action',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', actions.ids)],
        }

        return res
