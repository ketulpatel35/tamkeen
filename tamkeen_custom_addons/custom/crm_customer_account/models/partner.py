# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions

import logging


_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _name = _inherit = 'res.partner'

    def _default_customer(self):
        is_customer = self.env.context.get('crm_customer', False)
        return is_customer

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    is_company = fields.Boolean(string='Is a Company', default=lambda self: self._default_customer(),
                                help="Check if the contact is a company, otherwise it is a person")
    customer = fields.Boolean(string='Is a Customer', default=lambda self: self._default_customer(),
                              help="Check this box if this contact is a customer.")
    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                   column2='category_id', string='Industry', default=_default_category)

    def _customer_validation(self, vals, operation='create'):
        '''
        Validation on creating or editing new customer
        '''
        if operation is 'create':
            is_customer = vals.get('is_company', False)
            has_contact = vals.get('child_ids', None)
            if is_customer and not has_contact:
                raise exceptions.Warning(
                    _('You Cannot Create new customer without at least One contact !'))

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if self._context.get('crm_customer', False):
            self._customer_validation(vals, operation='create')
        return super(Partner, self).create(vals)
