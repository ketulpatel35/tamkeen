from odoo import fields, models, api


class PurchaseLineInvoice(models.TransientModel):
    _name = 'purchase.requisition.line_purchase'

    line_ids = fields.One2many('purchase.requisition.line_purchase.line',
                               'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields_list):
        """
        :param fields_list:
        :return:
        """
        res = super(PurchaseLineInvoice, self).default_get(fields_list)
        record_id =\
            self._context and\
            self._context.get('active_id', False) or False
        tender = self.env['purchase.requisition'].browse(record_id)
        lines = []
        for po_line in tender.purchase_ids:
            lines.append((0, 0, {
                'po_id': po_line.id,
                'name': po_line.name,
                'origin': po_line.origin,
                'state': po_line.state,
                'po_company_number': po_line.po_company_number,
                'amount_total': po_line.amount_total,
                'currency_id': po_line.currency_id.id,
            }))
        res.update({'line_ids': lines})
        return res

    @api.multi
    def generate_po(self):
        """
        :param self:
        :return:
        """
        po_ids = []
        record_id =\
            self._context and\
            self._context.get('active_id', False) or False
        tender_rec = self.env['purchase.requisition'].browse(record_id)
        for line_rec in self.line_ids:
            po_ids.append(line_rec.po_id.id)
        return tender_rec.generate_po(po_ids)


class PurchaseLineInvoiceLine(models.TransientModel):
    _name = 'purchase.requisition.line_purchase.line'

    po_id = fields.Many2one('purchase.order', 'Purchase order',
                            readonly=True)
    name = fields.Char(related='po_id.name', string='Name', readonly=True)
    origin = fields.Char(related='po_id.origin', string='Origin',
                         readonly=True)
    po_company_number = fields.Char(related='po_id.po_company_number',
                                    string='PO Company Number', readonly=True)
    state = fields.Selection(related='po_id.state', string='State',
                             readonly=True)
    amount_total = fields.Monetary(related='po_id.amount_total',
                                   string='Amount Total', readonly=True)
    wizard_id = fields.Many2one('purchase.requisition.line_purchase', 'Wizard')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  related='po_id.currency_id')
