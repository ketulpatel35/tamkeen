# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo import api, fields
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from datetime import datetime


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    # ('confirmed', 'Waiting Approval'),('approved', 'Purchase Confirmed'),
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        # ('confirmed', 'Waiting Approval'),
        # ('approved', 'Purchase Confirmed'),
        # ('except_picking', 'Shipping Exception'),
        # ('except_invoice', 'Invoice Exception'),
        ('budget_confirmed', 'Budget Confirmed'),
        ('to approve', 'CEO Approval'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft',
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

    po_company_number = fields.Char(string="PO Company Number", copy=False)
    from_budget_confirm = fields.Boolean('Budget Confirm')
    budget_user_id = fields.Many2one('res.users', string='Budget Confirm',
                                     readonly=True, copy=False)
    ceo_user_id = fields.Many2one('res.users', string='CEO Approval',
                                  readonly=True,
                                  copy=False)
    po_confirm_user_id = fields.Many2one('res.users', string='Confirmed User',
                                         readonly=True,
                                         copy=False)
    budget_confirm_date = fields.Datetime(
        string='Procurement Approval Date',
        readonly=True, copy=False)
    ceo_approval_date = fields.Datetime(string='CEO Approval Date',
                                        readonly=True,
                                        copy=False)
    po_confirm_date = fields.Datetime(string='Purchase Confirm Date',
                                      readonly=True,
                                      copy=False)
    return_date = fields.Date(string='Return Date', readonly=True, copy=False)
    returned_by = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        help='It will be automatically filled by the last user who returned '
             'the service.',
        copy=False)
    cancel_date = fields.Date(string='Cancel Date', readonly=True, copy=False)
    cancel_by = fields.Many2one(
        'res.users',
        string='Cancel By',
        readonly=True,
        help='It will be automatically filled by the last user who returned '
             'the service.',
        copy=False)
    set_to_draft = fields.Boolean(string='Set to Draft')

    @api.multi
    def bid_received(self):
        for rec in self:
            rec.state = 'bid'

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = window_action_ref = False
        if service_provider == 'purchase_order':
            window_action_ref = \
                'purchase.purchase_rfq'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def _set_email_template_context(self, data_pool,
                                    template_pool, email_to, dest_state,
                                    service_provider):
        context = dict(self._context)
        display_link = False
        base_url = self.env['ir.config_parameter'].\
            get_param('web.base.url.static')
        action_id = self._get_related_window_action_id(data_pool,
                                                       dest_state,
                                                       service_provider)
        if action_id:
            display_link = True
        context.update({
            'email_to': email_to,
            'base_url': base_url,
            'display_link': display_link,
            'action_id': action_id,
            'model': 'purchase.order'
        })
        return context

    @api.multi
    def _send_email(self, template_xml_ref, email_to, dest_state,
                    service_provider):
        context = dict(self._context)
        if template_xml_ref:
            addon_name = template_xml_ref.split('.')[0]
            template_xml_id = template_xml_ref.split('.')[1]
            data_pool = self.env['ir.model.data']
            template_pool = self.env['mail.template']
            if self:
                # rec_id = ids[0]
                template_id = \
                    data_pool.get_object_reference(addon_name,
                                                   template_xml_id)[1]
                template_rec = template_pool.browse(template_id)
                if template_rec:
                    email_template_context = self._set_email_template_context(
                        data_pool, template_pool, email_to,
                        dest_state, service_provider)
                    context.update(email_template_context)
                    template_rec.with_context(context).send_mail(
                        self.id, force_send=False)
            return True

    @api.multi
    def _get_service_req_approvals(self):
        # This list must be in the same workflow states order to help in
        # identifying/tracking the states (previous and destination).
        req_approvals = []
        for service in self:
            if service.requisition_id.type_id.purchase_bud_confirm:
                req_approvals.append('budget_confirmed')
            if service.requisition_id.type_id.ceo_approval:
                req_approvals.append('to approve')
            if service.requisition_id.type_id.po_confirm:
                req_approvals.append('purchase')
        return req_approvals

    @api.multi
    def is_transition_allowed(self, wkf_state_signal):
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for service in self:
                if wkf_state_signal in req_approvals or wkf_state_signal == \
                        'accepted':
                    return True
        return False

    @api.multi
    def _get_dest_state(self, service):
        dest_state = ''
        current_state = service.state
        service_states = ['draft', 'sent']  # to add the draft state
        req_approvals = self._get_service_req_approvals()
        if req_approvals:
            for approval in req_approvals:
                service_states.append(approval)
                # service_states.append('refused') # to add the refused state
                #  service_states.append('approved')  # to add the approved
                # state
        if current_state in service_states:
            current_state_index = service_states.index(
                current_state)  # req_approvals[service.state - 1]
            if current_state_index + 1 < len(service_states):
                dest_state = service_states[current_state_index + 1]
        return dest_state

    def _get_current_datetime(self):
        return datetime.now().strftime(OE_DTFORMAT)

    def _get_approval_info(self, service, dest_state):
        current_state = service.state
        # stage_id = self._get_related_stage_id(service, dest_state)
        # if not stage_id:
        #     raise Warning(_(
        #         "Stage ID not found, Please Configure Service Stages for "
        #         "%s") % (dest_state))
        # result = {'stage_id': stage_id.id}
        result = {}

        if current_state == 'draft':
            result.update({'state': dest_state,
                           'submitted_by': self.env.user.id,
                           'submit_date': self._get_current_datetime()})
        if current_state == 'sent':
            result.update({'state': dest_state,
                           'submitted_by': self.env.user.id,
                           'submit_date': self._get_current_datetime()})
        if current_state == 'budget_confirmed':
            result.update(
                {'state': dest_state, 'budget_user_id': self.env.user.id,
                 'budget_confirm_date': self._get_current_datetime()})
        if current_state == 'to approve':
            result.update(
                {'state': dest_state, 'ceo_user_id': self.env.user.id,
                 'ceo_approval_date': self._get_current_datetime()})
        if current_state == 'purchase':
            result.update(
                {'state': dest_state, 'po_confirm_user_id': self.env.user.id,
                 'po_confirm_date': self._get_current_datetime(),
                 'date_approve': date.today()})

        return result

    @api.multi
    def picking_ok(self):
        for rec in self:
            rec.state = 'done'

    @api.multi
    def invoice_ok(self):
        for rec in self:
            rec.state = 'done'

    @api.multi
    def purchase_budget_confirm(self):
        for rec in self:
            dest_state = self._get_dest_state(rec)
            if dest_state:
                rec.write(
                    self._get_approval_info(rec,
                                            dest_state))
                rec._send_email('purchase_config.'
                                'email_template_rfq_to_budget_approval',
                                None, dest_state, 'purchase_order')
            else:
                rec.write({'state': 'budget_confirmed'})

    @api.multi
    def button_draft(self):
        for rec in self:
            if rec.state == 'purchase':
                rec._send_email(
                    'purchase_config.'
                    'email_template_purchase_return_from_confirm_order',
                    None, 'draft', 'purchase_order')
                rec.write({'returned_by': self.env.user.id,
                           'return_date': self._get_current_datetime(),
                           'set_to_draft': True})
                ctx = self._context.copy()
                ctx.update({'from_darft': True})
                rec.with_context(ctx).button_cancel()
            if rec.state == 'budget_confirmed':
                rec._send_email(
                    'purchase_config.'
                    'email_template_purchase_return_from_budget_confirm',
                    None, 'draft', 'purchase_order')

        super(purchase_order, self).button_draft()

    @api.multi
    def button_confirm(self):
        for order in self:
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' or \
                    (order.company_id.po_double_validation == 'two_step' and
                     order.amount_total <
                     self.env.user.company_id.currency_id.compute(
                         order.company_id.po_double_validation_amount,
                         order.currency_id)):
                # button_approve have send notification
                order.button_approve(force=True)
            else:
                order.write({'state': 'to approve'})
                dest_state = 'to approve'
                order.write(order._get_approval_info(order,
                                                     dest_state))
                order._send_email(
                    'purchase_config.'
                    'email_template_confirm_order_to_ceo_approval',
                    None, dest_state, 'purchase_order')

            if not order.set_to_draft:
                pr = self.env['ir.sequence']. \
                    next_by_code('purchase.order.company.number')
                po_company_number = 'PO' + str(date.today().year) + str(pr)
                order.write({'po_company_number': order.name})
                order.write({'name': po_company_number})
            else:
                revno = self.revision_number
                val = {}
                if not order.po_company_number:
                    val = {'name': '%s' % (order.po_company_number),
                           'po_company_number': order.name}
                else:
                    po_company_number = ''
                    if revno == 1:
                        po_company_number = order.po_company_number
                    else:
                        po_company_number = order.po_company_number[:-3]
                    val = {'name': '%s-%02d' % (po_company_number, revno),
                           'po_company_number': order.name}
                order.write(val)
        return True

    @api.multi
    def button_approve(self, force=False):
        for order in self:
            dest_state = 'purchase'
            order.write(order._get_approval_info(order,
                                                 dest_state))
            order._send_email(
                'purchase_config.'
                'email_template_purchase_order_confirmed',
                None, dest_state, 'purchase_order')
        return super(purchase_order, self).button_approve(force)

    @api.multi
    def button_cancel(self):
        for order in self:
            if order.state == 'purchase':
                if not self._context.get('from_darft'):
                    order._send_email(
                        'purchase_config.'
                        'email_template_purchase_order_cancelation',
                        None, 'cancel', 'purchase_order')
                    order.write({'cancel_date': self._get_current_datetime(),
                                 'cancel_by': self.env.user.id})
        super(purchase_order, self).button_cancel()

        # @api.model
        # def _prepare_picking(self):
        #     res = super(purchase_order, self)._prepare_picking()
        #     if res and res.get('origin'):
        #         pr = self.env['ir.sequence']. \
        #             next_by_code('purchase.order.company.number')
        #         po_company_number = 'PO' + str(date.today().year) + str(pr)
        #         self.write({'po_company_number': po_company_number})
        #         res.update({'origin': po_company_number})
        #     return res

# class Report(models.Model):
#     _inherit = "report"
#
#     @api.model
#     def get_pdf(self, docids, report_name, html=None, data=None):
#         purchase = self.env['purchase.order'].browse(docids)
#         if (purchase.state == 'draft' or
#  purchase.state == 'sent') and report_name
#  == 'purchase.report_purchaseorder':
#             raise UserError(
#                 _('You cannot Print this report as it is in Draft State'))
#         res = super(
#             Report,
#             self).get_pdf(
#             docids,
#             report_name,
#             html=None,
#             data=None)
#         return res
