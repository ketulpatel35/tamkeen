# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _name = _inherit = 'crm.lead'

    user_id = fields.Many2one(
        'res.users',
        string='Account Manager',
        index=True, track_visibility='onchange',
        default=lambda self: self.env.user
    )

    client_type = fields.Selection([
        ('existing', 'Existing'),
        ('prospect', 'Prospect'),
        ('other', 'Other'),
    ], string='Client Type', default='existing')


    @api.multi
    def forward_to_account_manager(self):
        '''
        This function opens a window to compose
         an email, with the edi sale
          template message loaded by default
        '''

        self.ensure_one()
        
        template_id = self.env.ref(
                'crm_customer_account.email_update_forward_to_account_manager', False)
        compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form', False)
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'default_message_type': 'email',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }
