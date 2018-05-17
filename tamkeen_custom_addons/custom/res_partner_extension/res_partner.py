# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('country_id','company_id')
    def _get_local_country(self):
        for rec in self:
            if rec.country_id.code == rec.company_id.country_id.code:
                rec.is_local_sa = True
            else:
                rec.is_local_sa = False

    zakat_number = fields.Char('Zakat Number')
    is_local_sa = fields.Boolean('Is Local', compute=_get_local_country)

    @api.multi
    def _compute_supplier_payments_count(self):
        payments = self.env['account.payment']
        for partner in self:
            partner.supplier_payments_count = payments \
                .search_count([('partner_id', '=', partner.id)])

    supplier_payments_count = fields \
        .Integer(compute='_compute_supplier_payments_count',
                 string='# Supplier Payments')

    @api.model
    def create(self, vals):
        ir_model_data = self.env['ir.model.data']
        context = dict(self.env.context)
        display_link, wr_display_link = False, False
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        action_id = False
        window_action_ref = 'base.action_partner_supplier_form'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            action_id = ir_model_data.get_object_reference(
                addon_name, window_action_id)[1] or False
        if action_id:
            display_link = True
        context.update({
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'res.partner',
            'default_state': ''
        })
        if vals and vals.get('company_type') and vals.get('name'):
            if vals.get('company_type') == 'company':
                count = self.search_count([('company_type', '=', 'company'),
                                           ('name', '=', vals.get('name'))])
                if count > 0:
                    raise Warning(_('Warning ! \n'
                                    'the company name must be unique'))
        if self._context.get('default_supplier') and vals.get('company_type') =='company':
            if vals.get('name') and vals.get('name').isupper() ==False:
                raise Warning(_('Warning ! \n'
                                'the name must be capital letters only.'))
        self.env.context = context
        res = super(ResPartner, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        company_type = False
        name = False
        if vals.get('name') or vals.get('company_type'):
            if vals.get('company_type'):
                company_type = vals.get('company_type')
            else:
                company_type = self.company_type
            if vals.get('name'):
                name = vals.get('name')
            else:
                name = self.name
            if company_type and company_type == 'company':
                count = self.search_count([
                    ('company_type', '=', 'company'),
                    ('name', '=', name)])
                if count > 0:
                    raise Warning(_('Warning ! \n'
                                    'the company name must be unique'))
        if vals.get('name') or vals.get('company_type') == 'company':
            if self._context.get('default_supplier'):
                if vals.get('name').isupper() == False:
                    raise Warning(_('Warning ! \n'
                                    'the name must be capital letters only.'))
        res = super(ResPartner, self).write(vals)
        return res
