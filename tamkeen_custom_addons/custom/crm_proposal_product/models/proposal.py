# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions
import odoo.addons.decimal_precision as dp

import logging


_logger = logging.getLogger(__name__)


class ProposalLine(models.Model):
    _name = _inherit = 'crm.proposal.line'

    @api.depends('product_uom_qty', 'price_unit', 'discount')
    def _compute_amount(self):
        for line in self:
            price = (line.price_unit * line.product_uom_qty) * \
                (1 - (line.discount or 0.0) / 100.0)
            line.update({
                'price_total': price,
            })

    price_unit = fields.Float('Item Price', required=True, digits=dp.get_precision(
        'Product Price'), default=0.0)

    price_total = fields.Monetary(
        compute='_compute_amount', string='Total', readonly=True, store=True)


    product_id = fields.Many2one('product.product',
        string='Product',
        domain=[('sale_ok', '=', True)],
        change_default=True,
        ondelete='restrict',
        required=True,
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision(
        'Product Unit of Measure'),
        required=True,
        default=1.0,
    )
    product_uom = fields.Many2one('product.uom',
        string='Unit of Measure',
        required=True,
    )

    @api.multi
    def _get_display_price(self, product):
        final_price, rule_id = self.proposal_id.pricelist_id.get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.proposal_id.partner_id)
        context_partner = dict(
            self.env.context, partner_id=self.proposal_id.partner_id.id, date=self.proposal_id.actual_release_date)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(
            self.product_id, rule_id, self.product_uom_qty, self.product_uom, self.proposal_id.pricelist_id.id)
        if currency_id != self.proposal_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(
                context_partner).compute(base_price, self.proposal_id.pricelist_id.currency_id)
        return max(base_price, final_price)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [
            ('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.proposal_id.partner_id.lang,
            partner=self.proposal_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.proposal_id.planned_release_date,
            pricelist=self.proposal_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}


        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self.update(vals)

        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.proposal_id.pricelist_id and self.proposal_id.partner_id:
            product = self.product_id.with_context(
                lang=self.proposal_id.partner_id.lang,
                partner=self.proposal_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.proposal_id.actual_release_date,
                pricelist=self.proposal_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            self.price_unit = self._get_display_price(product)

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                price, rule_id = pricelist_item.base_pricelist_id.with_context(
                        uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(
            product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id


class Proposal(models.Model):
    _name = _inherit = 'crm.proposal'

    @api.depends('line_ids.product_uom_qty', 'line_ids.discount', 'line_ids.price_unit', 'discount')
    def _amount_all(self):
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
    
    total = fields.Monetary(
        string='Total', compute='_amount_all', currency_field='currency_id')

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={
                                   'new': [('readonly', False)],}, help="Pricelist for current Proposal.")
    currency_id = fields.Many2one(
        "res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    def _get_revision_line_m2o_fields_list(self):
        LIST = super(Proposal, self)._get_revision_line_m2o_fields_list()
        return LIST + [
            'product_id',
            'product_uom',
        ]

    def _get_revision_line_fields_list(self):
        LIST = super(Proposal, self)._get_revision_line_fields_list()
        return LIST + [
            'product_id',
            'product_uom',
        ]

    def _get_revision_m2o_fields_list(self):
        LIST = super(Proposal, self)._get_revision_m2o_fields_list()
        return LIST + [
            'pricelist_id',
        ]

    def _get_revision_fields_list(self):
        LIST = super(Proposal, self)._get_revision_fields_list()
        return LIST + [
            'pricelist_id',
        ]
