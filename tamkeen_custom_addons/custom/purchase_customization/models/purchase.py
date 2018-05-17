# -*- encoding: utf-8 -*-

from odoo import fields, api, models


class PurchaseCancelReason(models.TransientModel):
    _name = 'purchase.cancel.reason'

    name = fields.Text(string='Cancel Reason')
    purchase_id = fields.Many2one('purchase.order', string='Purchase')

    @api.model
    def default_get(self, field_list):
        res = super(PurchaseCancelReason, self).default_get(field_list)
        if self._context and self._context.get('active_id'):
            res['purchase_id'] = self._context.get('active_id')
        return res

    @api.multi
    def proceed(self):
        for this in self:
            this.purchase_id.cancel_reason = this.name


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        user_rec = self
        if self._context and self._context.get('po_officer'):
            value = self.search([])
            for rec in value:
                if rec.has_group('purchase.group_purchase_user'):
                    user_rec += rec
            return user_rec.name_get()
        return super(ResUsers, self). \
            name_search(name=name, args=args, operator=operator, limit=limit)


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def set_invoice_received(self):
        for rec in self:
            if rec.invoice_status == 'invoiced':
                rec.is_invoice_received = True

    quotation_ref = fields.Char('Quotation Reference')
    rfp_ref_num = fields.Integer('RFP Reference Number')
    notes = fields.Html(string='Notes')
    is_invoice_received = fields.Boolean(string='Invoice Received',
                                         compute='set_invoice_received')
    validate_by_user_id = fields.Many2one('res.users', string='Validate By')
    cancel_reason = fields.Text(string='Cancel Reason')
    bid_received_on = fields.Date('Bid Received On')
    bid_valid_untill = fields.Date('Bid Valid Untill')

    @api.model
    def create(self, vals):
        """
        set sequence number in order line
        :param vals:
        :return:
        """
        count = 0
        if vals and vals.get('order_line'):
            for line in vals.get('order_line'):
                count += 1
                vals.get('order_line')[count - 1][2]['sn_number'] = count
        return super(purchase_order, self).create(vals)

    @api.multi
    def print_quotation(self):
        """
        send notification on RFQ stage.
        :return:
        """
        for rec in self:
            if rec.requisition_id and rec.requisition_id.type_id and \
                    rec.requisition_id.type_id.po_rfq:
                dest_state = 'sent'
                rec._send_email('purchase_customization.'
                                'email_template_po_to_rfq',
                                None, dest_state, 'purchase_order')
        res = super(purchase_order, self).print_quotation()
        return res

    @api.multi
    def bid_received(self):
        """
        send notification on bid received.
        :return:
        """
        for rec in self:
            if rec.requisition_id and rec.requisition_id.type_id and \
                    rec.requisition_id.type_id.po_bid_received:
                dest_state = 'bid'
                rec._send_email('purchase_customization.'
                                'email_template_po_rfq_to_bid_received',
                                None, dest_state, 'purchase_order')
        res = super(purchase_order, self).bid_received()
        return res

    @api.multi
    def purchase_budget_confirm(self):
        """
        send notification on budget confirm.
        :return:
        """
        for rec in self:
            if rec.requisition_id and rec.requisition_id.type_id and \
                    rec.requisition_id.type_id.po_bud_confirm:
                dest_state = 'budget_confirmed'
                rec._send_email('purchase_customization.'
                                'email_template_po_bid_to_bud_confirm',
                                None, dest_state, 'purchase_order')
        res = super(purchase_order, self).purchase_budget_confirm()
        return res

    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        self.validate_by_user_id = self.env.user.id
        return res

    @api.multi
    def button_cancel(self):
        super(purchase_order, self).button_cancel()

        return {
            'name': 'Cancel Reason',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.cancel.reason',
            'view_id': self.env.ref(
                'purchase_customization.purchase_cancel_reason_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def name_get(self):
        if self._context.get('only_search_by_po'):
            result = []
            for record in self:
                if record.po_company_number:
                    result.append(
                        (record.id, record.po_company_number))
            return result
        else:
            return super(purchase_order, self).name_get()


class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'

    product_service_description = fields.Text('Product/Service Description')
    remark = fields.Text('Remarks')

    @api.multi
    def _get_line_count(self):
        for rec in self:
            if rec.line_ids:
                rec.line_count = len(rec.line_ids)

    line_count = fields \
        .Integer(compute='_get_line_count', string='Total number of items')

    @api.model
    def create(self, vals):
        """
        set sequence
        :param vals:
        :return:
        """
        count = 0
        if vals and vals.get('line_ids'):
            for line in vals.get('line_ids'):
                count += 1
                vals.get('line_ids')[count - 1][2]['sn_number'] = count
        return super(purchase_requisition, self).create(vals)


class purchase_requisition_line(models.Model):
    _inherit = 'purchase.requisition.line'

    sn_number = fields.Integer(string='Serial Number', default=1)

    @api.multi
    def unlink(self):
        """
        set sequence number
        :return:
        """
        for record in self:
            if record.requisition_id:
                count = 1
                for record_line in record.requisition_id.line_ids:
                    if record_line.id != record.id:
                        record_line.sn_number = count
                        count += 1
        return super(purchase_requisition_line, self).unlink()

    @api.model
    def default_get(self, fields_list):
        """
        set sequence number
        :param fields_list:
        :return:
        """
        res = super(purchase_requisition_line, self) \
            .default_get(fields_list)
        if self._context.get('line_ids'):
            count = len(self._context.get('line_ids'))
            count += 1
            res.update({'sn_number': count})
        if not self._context.get('line_ids'):
            res.update({'sn_number': 1})
        return res


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'
    sn_number = fields.Integer(string='Serial Number', default=1)
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ'),
        # ('bid', 'Bid Received'),
        # ('confirmed', 'Waiting Approval'),
        # ('approved', 'Purchase Confirmed'),
        # ('except_picking', 'Shipping Exception'),
        # ('except_invoice', 'Invoice Exception'),
        ('budget_confirmed', 'Budget Confirmed'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft',
        related='order_id.state',
        track_visibility='onchange',
        help="The status of the purchase order or the quotation request. "
             "A request for quotation is a purchase order in a 'Draft' status."
             "Then the order has to be confirmed by the user, the status "
             "switch"
             "to 'Confirmed'. Then the supplier must confirm the order to "
             "change "
             "the status to 'Approved'. When the purchase order is paid and "
             "received, the status becomes 'Done'. If a cancel action occurs "
             "in"
             "the invoice or in the receipt of goods, the status becomes "
             "in exception.", )

    @api.multi
    def unlink(self):
        """
        set serial number for order line
        :return:
        """
        for record in self:
            if record.order_id:
                count = 1
                for record_line in record.order_id.order_line:
                    if record_line.id != record.id:
                        record_line.sn_number = count
                        count += 1
        return super(purchase_order_line, self).unlink()

    @api.model
    def default_get(self, fields_list):
        """
        set serial number for order line
        :param fields_list:
        :return:
        """
        res = super(purchase_order_line, self) \
            .default_get(fields_list)
        if self._context.get('order_line'):
            count = len(self._context.get('order_line'))
            count += 1
            res.update({'sn_number': count})
        if not self._context.get('order_line'):
            res.update({'sn_number': 1})
        return res


class PurchaseRequisitionType(models.Model):
    _inherit = 'purchase.requisition.type'

    po_rfq = fields.Boolean('PO RFQ')
    po_bid_received = fields.Boolean('PO Bid Received')
    po_bud_confirm = fields.Boolean('PO Budget Confirm')
