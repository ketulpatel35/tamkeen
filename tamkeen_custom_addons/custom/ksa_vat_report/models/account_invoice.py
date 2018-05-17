# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    date_invoice = fields.Date(related='invoice_id.date_invoice',
                               string='Bill Date')
    state = fields.Selection(related='invoice_id.state',
                             string='State')


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if args is None:
            args = []
        if context.get('search_default_invoice_line_tax_ids', False):
            invoice_line_ids = []
            if context['search_default_invoice_line_tax_ids']:
                self._cr.execute("""
                    select invoice_line_id from account_invoice_line_tax where
                    tax_id in (%s)
                """ % (','.join(map(str, context['search_default_invoice_line_tax_ids']))))
                invoice_line_ids = [line[0] for line in self._cr.fetchall()]
                args += [('id', 'in', invoice_line_ids)]
        if context.get('validated', False):
            args += [('state', 'in', ('open', 'paid'))]
        return super(AccountInvoiceLine, self).search(args, offset=offset,
                                                      limit=limit,
                                                      order=order,
                                                      count=count)
