from datetime import datetime
from num2words import num2words
from odoo.report import report_sxw
from odoo import models, api
from odoo.api import Environment
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT


class PurchaseOrderReportParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(PurchaseOrderReportParser, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_order_total': self._get_order_total,
            'today': datetime.strftime(datetime.now(), OE_DFORMAT),
            'get_payment_status': self.get_payment_status,
            'get_related_invoice': self.get_related_invoice,
            'get_invoice_related_payment': self.get_invoice_related_payment,
        })

    def _get_order_total(self, order_total):
        return num2words(order_total)

    @api.model
    def get_payment_status(self, record):
        """

        :param record:
        :return:
        """
        self.env = Environment(
            record._cr, record._uid, record._context)
        purchase_orders_rec = record
        account_invoice = self.env['account.invoice'].search([
            ('origin', '=', purchase_orders_rec.name)])
        paid_amount = 0
        paid_count = 0
        status = ''
        for invoice in account_invoice:
            if (invoice.state == "paid"):
                paid_amount = paid_amount + invoice.amount_total
            else:
                if (invoice.state == "open"):
                    paid_amount = paid_amount + (
                        invoice.amount_total - invoice.residual)
            for item in invoice.payment_ids:
                if (item.state == 'valid'):
                    paid_count = paid_count + 1
        if (paid_amount == purchase_orders_rec.amount_total):
            status = 'Paid'
        else:
            if (paid_amount == 0):
                status = 'UnPaid'
            else:
                status = 'Partially'
        data = {
            'paid_amount': paid_amount,
            'paid_count': paid_count,
            'status': status
        }
        return data

    @api.model
    def get_related_invoice(self, purchase_rec):
        """
        get purchase order related invoice and
        return list of invoice record.
        --------------------------------
        :param record:
        :return:
        """
        inv_rec_list = []
        self.env = Environment(purchase_rec._cr,
                               purchase_rec._uid,
                               purchase_rec._context)
        for inv_rec in self.env['account.invoice'].search(
                [('origin', '=', purchase_rec.name), ('state', 'not in',
                                                      ['draft'])]):
            inv_rec_list.append(inv_rec)
        return inv_rec_list

    @api.model
    def get_invoice_related_payment(self, purchase_rec):
        """
        get purchase order related invoice and
        return list of invoice record.
        --------------------------------
        :param record:
        :return:
        """
        payment_rec_list = []
        self.env = Environment(
            purchase_rec._cr, purchase_rec._uid, purchase_rec._context)
        for inv_rec in self.env['account.invoice'].search(
                [('origin', '=', purchase_rec.name)]):
            if inv_rec.amount_total - inv_rec.residual != 0:
                for payment_rec in self.env['account.payment'].search(
                        [('id', 'in', inv_rec.payment_ids.ids)]):
                    if payment_rec not in payment_rec_list:
                        payment_rec_list.append(payment_rec)

        return payment_rec_list


class PurchaseOrderReportAbs(models.AbstractModel):
    _name = 'report.purchase_order_report.purchase_payment_report_template'

    _inherit = 'report.abstract_report'

    _template = 'purchase_order_report.purchase_payment_report_template'

    _wrapped_report_class = PurchaseOrderReportParser


class PurchaseOrderDetailsParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(PurchaseOrderDetailsParser, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'num2words': self.num2words
        })

    @api.model
    def num2words(self, amount):
        return num2words(amount)


class PurchaseOrderDetailsReportAbs(models.AbstractModel):
    _name = 'report.purchase_order_report.po_view_report'

    _inherit = 'report.abstract_report'

    _template = 'purchase_order_report.po_view_report'

    _wrapped_report_class = PurchaseOrderDetailsParser
