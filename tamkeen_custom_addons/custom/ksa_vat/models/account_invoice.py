from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.depends('product_id', 'discount', 'price_unit',
                 'invoice_line_tax_ids', 'quantity')
    def _compute_tax_amount(self):
        """
        Compute the tax amounts of the Invoice line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price, line.currency_id,
                                            line.quantity,
                                            product=line.product_id,
                                            partner=line.invoice_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
            })

    price_tax = fields.Monetary(compute='_compute_tax_amount', string='Tax '
                                                                      'Amount',
                                readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_tax_amount',
                                  string='Total', readonly=True, store=True)
