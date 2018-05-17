from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import Warning


class InvoicesApprovalLine(models.Model):
    _name = 'invoices.approval.line'

    @api.multi
    def compute_amount(self):
        """
        :return:
        """
        for rec in self:
            if rec.invoice_id:
                rec.amount_total = rec.invoice_id.amount_total
                rec.residual = rec.invoice_id.residual

    invoice_id = fields.Many2one('account.invoice', 'Invoice Id')
    partner_id = fields.Many2one('res.partner',
                                 string='Partner')
    date_invoice = fields.Date('Invoice Date')
    number = fields.Char('number')
    reference = fields.Char('Reference')
    date_due = fields.Date('Due Date')
    origin = fields.Char('Origin')
    currency_id = fields.Many2one('res.currency')
    amount_total = fields.Monetary(compute='compute_amount')
    residual = fields.Monetary('Amount Due', compute='compute_amount')
    confirm_amount = fields.Boolean('confirm Amount')
    payment_amount = fields.Float('Payment Amount')
    bill_batch_app_id = fields.Many2one('bill.batch.approval')


class VendorBillBatchApproval(models.Model):
    _name = 'bill.batch.approval'

    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def compute_total_payable_amount(self):
        """
        compute total payable amount
        :return:
        """
        for rec in self:
            total_amount = 0
            for invoice_rec in rec.inv_app_ids:
                total_amount += invoice_rec.payment_amount
            rec.total_pay = total_amount

    name = fields.Char('Name', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Vendor Id',
                                 track_visibility='onchange')
    reference = fields.Char('Reference', track_visibility='onchange')
    date = fields.Date('Date', track_visibility='onchange')
    # invoice_line_ids = fields.One2many('account.invoice',
    #                                    'vendor_batch_pay_id')
    inv_app_ids = fields.One2many('invoices.approval.line',
                                  'bill_batch_app_id', 'Invoice Lines',
                                  track_visibility='onchange')
    total_pay = fields.Float('Total Amount',
                             compute='compute_total_payable_amount')
    currency_id = fields.Many2one('res.currency', 'Currency')
    vendor_batch_payment_ids = fields.One2many('vendor.batch.payment.line',
                                               'bill_batch_app_id',
                                               'Batch Approval Line')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'),
                              ('done', 'Done')], string='Status', index=True,
                             readonly=True, default='draft',
                             track_visibility='onchange', copy=False)

    @api.multi
    def unlink(self):
        """
        can not delete record which is in open or done
        :return:
        """
        for rec in self:
            if rec.state in ['open', 'done']:
                raise Warning('Can not delete a record which is in Open or '
                              'Done state')
        return super(VendorBillBatchApproval, self).unlink()

    @api.multi
    def confirm_payment_amount(self):
        """
        confirm payment amount.
        :return:
        """
        for rec in self:
            vendor_batch_data = {}
            for inv_rec in rec.inv_app_ids:
                inv_rec.invoice_id.payment_amount = inv_rec.payment_amount
                inv_rec.confirm_amount = True
                if inv_rec.partner_id.id not in vendor_batch_data:
                    vendor_batch_data.update({inv_rec.partner_id.id: [
                        inv_rec.invoice_id.id]})
                else:
                    vendor_batch_data[inv_rec.partner_id.id].append(
                        inv_rec.invoice_id.id)
            if vendor_batch_data:
                for vendor_id, inv_list in vendor_batch_data.items():
                    vendor_batch_payment_rec = \
                        self.env['vendor.batch.payment.line'].create({
                            'partner_id': vendor_id,
                            'date': datetime.today().date(),
                            'bill_batch_app_id': rec.id})
                    vendor_batch_payment_rec.invoice_ids = [(6, 0, inv_list)]
            rec.state = 'open'


class VendorBatchPaymentLine(models.Model):
    _name = 'vendor.batch.payment.line'

    @api.multi
    def compute_amount_calculation(self):
        """
        compute total amount and total due amount of vendor all selected
        invoice.
        :return:
        """
        for rec in self:
            total_amount = total_due = total_pay = 0
            for inv_rec in rec.invoice_ids:
                total_amount += inv_rec.amount_total
                total_due += inv_rec.residual
                total_pay += inv_rec.payment_amount
            rec.total_amount = total_amount
            rec.total_due = total_due
            rec.total_pay = total_pay

    partner_id = fields.Many2one('res.partner', 'Vendor Id')
    bill_batch_app_id = fields.Many2one('bill.batch.approval', 'Batch Id')
    date = fields.Date('Date')
    invoice_ids = fields.Many2many('account.invoice', 'rel_vb_pay_invoice',
                                   'vb_pay_id', 'inv_id', 'Invoices')
    is_batch = fields.Boolean(string="Is Batch approval")
    total_amount = fields.Float('Total Amount',
                                compute='compute_amount_calculation')
    total_due = fields.Float('Total Due', compute='compute_amount_calculation')
    total_pay = fields.Float('Payment Amount',
                             compute='compute_amount_calculation')
    account_payment_id = fields.Many2one('account.payment', 'Payment')

    @api.multi
    def multi_invoice_registered_payment(self):
        """
        vendor multiple invoice register payment
        :return:
        """
        context = dict(self._context)
        view_id = self.env.ref('account_batch_payment_diff.'
                               'view_account_payment_register').id
        for rec in self:
            inv_amount_dict = {}
            for inv_rec in rec.invoice_ids:
                inv_amount_dict.update({inv_rec.id: inv_rec.payment_amount})
            context.update({'active_model': 'account.invoice',
                            'active_ids': rec.invoice_ids.ids,
                            'inv_amount_dict': inv_amount_dict,
                            'vendor_batch_payment_id': rec.id,
                            'to_pay': rec.total_pay})
        return {
            'name': _("Register Payment For multiple invoices"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.register.payments',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    vendor_batch_pay_id = fields.Many2one('bill.batch.approval',
                                          string='Batch Payment Id',
                                          copy=False)
    payment_amount = fields.Float('Payment Amount', default=0)
