# -*- coding: utf-8 -*-
from openerp import api, _, fields, models
from odoo.exceptions import Warning


class AccountInvoiceReversal(models.Model):
    _inherit = "account.invoice"

    reversal_move_id = fields.Many2one('account.move',
                                       string='Reversal Journal Entry',
                                       copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('confirm', 'Waiting Confirmation'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('reversed', 'Reversed'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new "
             "and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not "
             "have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, "
             "an invoice number is generated. It stays in the open status "
             "till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is "
             "paid. Its related journal entries may or may not be "
             "reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.multi
    def generate_reversal_entry(self):
        for rec in self:
            if rec.payment_move_line_ids:
                raise Warning(_('Please Unreconcile related payment before '
                                'reverse the invoice Journal Entry'))
            view = self.env.ref('account.view_account_move_reversal')
            context = self._context.copy()
            context.update({'default_invoice_id': rec.id})
            return {
                'name': _('Reversal and Reconcile'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move.reversal',
                'views': [(view.id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    reason = fields.Text('Reason for reversal', required=True)
    invoice_id = fields.Many2one('account.invoice', string='Invoice')

    @api.multi
    def reconcile_reversal_journal_entry(self, move_rec, reversal_move_rec,
                                         account_rec):
        """
        :param move_rec:
        :param reversal_move_rec:
        :param account_rec:
        :return:
        """
        move_lines = []
        [move_lines.append(line_rec.id) for line_rec in move_rec.line_ids if
         line_rec.account_id.id == account_rec.id]
        [move_lines.append(line_rec.id) for line_rec in
         reversal_move_rec.line_ids if line_rec.account_id.id ==
         account_rec.id]
        ctx = self._context.copy()
        ctx.update({'active_ids':move_lines})
        self.env['account.move.line.reconcile'].with_context(
            ctx).trans_rec_reconcile_full()
        return True

    @api.multi
    def reverse_moves(self):
        if not self.invoice_id:
            return super(AccountMoveReversal, self).reverse_moves()

        ac_move_ids = self.invoice_id.move_id.id
        res = self.env['account.move'].browse(ac_move_ids).reverse_moves(
            self.date, self.journal_id or False)
        if res:
            self.invoice_id.reversal_move_id = res[0]
            self.reconcile_reversal_journal_entry(
                self.invoice_id.move_id, self.invoice_id.reversal_move_id,
                self.invoice_id.account_id)
            self.invoice_id.state = 'reversed'
            type = ''
            if self._context.get('type')== 'out_invoice':
                type = 'Customer Invoice'
            if self._context.get('type') == 'in_invoice':
                type = 'Vendor Bill'
            message = _("This %s has been revered with reason: "
                        "%s") \
                      % \
                      (type,",".join([str(self.reason)]))
            self.invoice_id.message_post(body=message)
        return {'type': 'ir.actions.act_window_close'}
