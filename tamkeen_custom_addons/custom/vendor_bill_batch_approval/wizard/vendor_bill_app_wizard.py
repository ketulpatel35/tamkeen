from odoo import api, models, _
from odoo.exceptions import Warning
from datetime import date


class VendorBillBatchAppWizard(models.TransientModel):
    _name = 'vendor.bill.batch.approval'

    @api.multi
    def vendor_bill_batch_approval(self):
        """
        create vendor bill batch approval record.
        :return:
        """
        if self._context and self._context.get('active_ids'):
            partner_id_list = []
            inv_rec_list = []
            reference = ''
            partner_id = False
            if not self._context.get('active_ids'):
                raise Warning(_('please select at least one invoice to '
                                'proceed next step!'))
            currency_id = False
            for inv_rec in self.env['account.invoice'].browse(
                    self._context.get('active_ids')):
                if not currency_id:
                    currency_id = inv_rec.currency_id.id
                # check for diff vendor have diff currency then what to do?
                if currency_id != inv_rec.currency_id.id:
                    raise Warning(_('Selected Invoice Currency should be '
                                    'Same !'))
                if inv_rec.type != 'in_invoice':
                    raise Warning(_('invoice type should be vendor bill '
                                    'only.!'))
                if inv_rec.state != 'open':
                    raise Warning(_('You can select only open invoices.'))
                else:
                    if not inv_rec.amount_total == 0:
                        if inv_rec.partner_id.id:
                            partner_id_list.append(inv_rec.partner_id.id)
                            inv_rec.payment_amount = 0
                            inv_rec_list.append(inv_rec)
            if inv_rec_list:
                seq = self.env['ir.sequence'].next_by_code('vendor.bill.multi')
                batch_approval_data = {'name': seq, 'partner_id': partner_id,
                                       'reference': reference,
                                       'date': date.today(),
                                       'currency_id': currency_id}
                bill_batch_approval_rec = \
                    self.env['bill.batch.approval'].create(batch_approval_data)
                for inv_rec in inv_rec_list:
                    self.env['invoices.approval.line'].create({
                        'invoice_id': inv_rec.id,
                        'bill_batch_app_id': bill_batch_approval_rec.id,
                        'partner_id': inv_rec.partner_id.id,
                        'date_invoice': inv_rec.date_invoice,
                        'number': inv_rec.number,
                        'reference': inv_rec.reference,
                        'date_due': inv_rec.date_due,
                        'origin': inv_rec.origin,
                        'currency_id': inv_rec.currency_id.id,
                    })
        return True
