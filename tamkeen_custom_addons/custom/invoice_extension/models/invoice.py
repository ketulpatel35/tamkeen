# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('confirm', 'Waiting Confirmation'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True,
        readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a"
             " new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,"
             "invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,"
             "a invoice number is generated.Its in open status till "
             "user does not pay invoice.\n"
             " * The 'Paid' status is set automatically when "
             "the invoice is paid. Its related journal entries "
             "may or may not be reconciled.\n"
             " * The 'Cancelled' status is used "
             "when user cancel invoice.")
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')

    # We comment code because of some data issue will work on it letter
    # @api.onchange('invoice_line_ids')
    # def onchange_invoice_line_ids(self):
    #     if self.invoice_line_ids:
    #         for line in self.invoice_line_ids:
    #             if self.account_analytic_id != line.account_analytic_id:
    #                 self.purchase_id = False
    #                 raise Warning(
    #                     _('You cant select different analytic id after '
    #                       'generating invoice line'
    #                       ))

    @api.multi
    def get_related_purchase_order(self):
        domain = []
        for rec in self:
            if rec.origin:
                domain = [('name', '=', rec.origin)]
            return {
                'name': _('Purchase Order'),
                'view_type': 'form',
                "view_mode": 'tree,form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'domain': domain
            }

    @api.multi
    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.multi
    def submit_to_fi_manager(self):
        for rec in self:
            rec.state = 'confirm'

    @api.multi
    def _get_related_window_action_id(self, data_pool,
                                      dest_state, service_provider):
        window_action_id = window_action_ref = False
        if service_provider == 'account_invoice':
            window_action_ref = \
                'purchase.purchase_open_invoice'
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
            'model': 'account.invoice'
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
    def submit_to_first_validate(self):
        """First Validation"""
        for rec in self:
            rec.state = 'submit'

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open,
        # so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(
                lambda inv: inv.state not in ['proforma2',
                                              'draft',
                                              'confirm']):
            raise UserError(_("Invoice must be in draft or "
                              "Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()
