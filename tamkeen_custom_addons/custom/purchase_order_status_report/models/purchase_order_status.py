# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
from odoo.exceptions import UserError
import datetime as dt
import base64
from datetime import datetime
from cStringIO import StringIO
from odoo.exceptions import UserError
try:
    import xlwt
except ImportError:
    xlwt = None

class PurchaseOrderStatusXlsReport(models.Model):
    _name = 'purchase.order.status.xls.report'

    @api.model
    def set_header(self, worksheet):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """
        worksheet.row(0).height = 600
        worksheet.row(1).height = 350
        worksheet.row(2).height = 320
        worksheet.row(3).height = 320
        t_col = 17
        for for_col in range(0, t_col):
            worksheet.col(for_col).width = 200 * 30
        s0 = xlwt.easyxf(
            'font: bold 1,height 280 ,colour green;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour aqua,'
            'fore_colour gray40')
        header_0 = "Purchase Order Status Report"
        worksheet.write_merge(0, 0, 0, 11, header_0, s0)

        s4 = xlwt.easyxf(
            'font: bold 1,height 220, colour white;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour gray50,'
            'fore_colour gray50'
        )
        header_4 = ['PR Number',
                    'Reference',
                    'PO Company Number',
                    # 'Order Date',
                    'Approved Date',
                    'Supplier',
                    'Cost Center',
                    'Beneficiary',
                    'Currency',
                    'Total PO Amount',
                    '# of Invoice Received',
                    'Amount of Invoices',
                    'Not Invoiced',
                    ]
        h_12_col = 0
        for h_12 in header_4:
            worksheet.write(1, h_12_col, label=h_12, style=s4)
            h_12_col += 1

        return worksheet

    @api.multi
    def _get_po_records(self, record):
        """
        get details
        :param period_id:
        :return:
        """
        res = []
        data = {}

        for record_line in record:
            pr = record_line.requisition_id and record_line.requisition_id.name
            cost_centre_id = record_line.requisition_id and \
                             record_line.requisition_id.cost_centre_id and \
                             record_line.requisition_id.cost_centre_id.name or 'N/A'
            data = {
                # 'PR_Number': record_line.partner_ref or 'N/A',
                'PR_Number': pr or 'N/A',
                'Reference': record_line.name or 'N/A',
                'PO_Company_Number': record_line.po_company_number or 'N/A',
                # 'Order_Date': record_line.date_order,
                'Approved_Date': record_line.date_approve or 'Nill',
                'Supplier': record_line.partner_id.name or 'N/A',
                # 'Cost_Center': record_line.cost_centre_id.name or 'N/A',
                'Cost_Center': cost_centre_id,
                'Benificiery':
                    record_line.requisition_id.other_details or 'N/A',
                'Currency': record_line.currency_id.name,
                'PO_Amount': record_line.amount_total,
                'No_of_Invoice_Received': 0,
                'Amount_of_Invoices': 0,
                'Not_Invoiced': 0,
                'default_Paid_invoices': 0,
                'default_Non_Paid_Invoices': 0,
                'Paid_invoices': 0,
                'Non_Paid_Invoices': 0,
            }
            amt_invoice = amt_not_invoice \
                = amt_paid = amt_not_paid = invoice_count = 0

            for invoice_id in record_line.invoice_ids:
                if invoice_id.state not in ('draft', 'cancel'):
                    invoice_count += 1
                    amt_invoice += invoice_id.amount_total
                if invoice_id.state == 'paid':
                    amt_paid += invoice_id.amount_total
                    amt_not_paid += (amt_invoice - amt_paid)
            if record_line.amount_total > 0:
                amt_not_invoice += (record_line.amount_total -
                                    amt_invoice)
            data.update({
                'No_of_Invoice_Received': invoice_count,
                'Amount_of_Invoices': amt_invoice,
                'Not_Invoiced': amt_not_invoice,
                'default_Paid_invoices': amt_paid,
                'default_Non_Paid_Invoices': amt_not_paid,
                'Paid_invoices': amt_paid,
                'Non_Paid_Invoices': amt_not_paid,
            })
            res.append(data)

        return res

    @api.model
    def set_line_data(self, po_status_record, worksheet):
        sheet_row = 4
        sheet_col = 0
        last_row = 0

        total = {
            'total_po_amount': 0,
            'total_no_of_invoice_received': 0,
            'total_amount_of_invoices': 0,
            'total_not_invoiced': 0,
            'default_total_of_paid_invoices': 0,
            'default_total_of_non_paid_invoices': 0,
            'total_of_paid_invoices': 0,
            'total_of_non_paid_invoices': 0,
        }
        total_po_amount = \
            total_no_of_invoice_received = \
            total_amount_of_invoices = total_not_invoiced = \
            total_of_paid_invoices = total_of_non_paid_invoices = 0

        for rec in po_status_record:
            total_po_amount +=\
                rec.get('PO_Amount') if rec.get('PO_Amount') else 0
            total_no_of_invoice_received +=\
                rec.get('No_of_Invoice_Received') if rec.get(
                    'No_of_Invoice_Received') else 0
            total_amount_of_invoices += rec.get(
                'Amount_of_Invoices') if rec.get('Amount_of_Invoices') else 0
            total_not_invoiced += rec.get(
                'Not_Invoiced') if rec.get('Not_Invoiced') else 0
            total_of_paid_invoices += rec.get(
                'Paid_invoices') if rec.get('Paid_invoices') else 0
            total_of_non_paid_invoices += rec.get(
                'Non_Paid_Invoices') if rec.get('Non_Paid_Invoices') else 0

        total.update({
            'total_po_amount': total_po_amount,
            'total_no_of_invoice_received': total_no_of_invoice_received,
            'total_amount_of_invoices': total_amount_of_invoices,
            'total_not_invoiced': total_not_invoiced,
            'default_total_of_paid_invoices': total_of_paid_invoices,
            'default_total_of_non_paid_invoices': total_of_non_paid_invoices,
            'total_of_paid_invoices': total_of_paid_invoices,
            'total_of_non_paid_invoices': total_of_non_paid_invoices,
        })
        s4 = xlwt.easyxf(
            'font: bold 1,colour blue;'
            'borders: left thin, right thin, top thin, bottom thin;'
        )
        for slip_data in po_status_record:
            worksheet.write(sheet_row, 0, label=slip_data['PR_Number'])
            worksheet.write(sheet_row, 1, label=slip_data['Reference'])
            worksheet.write(sheet_row, 2, label=slip_data['PO_Company_Number'])
            # worksheet.write(sheet_row, 3, label=slip_data['Order_Date'])
            worksheet.write(sheet_row, 3, label=slip_data['Approved_Date'])
            worksheet.write(sheet_row, 4, label=slip_data['Supplier'])
            worksheet.write(sheet_row, 5, label=slip_data['Cost_Center'])
            worksheet.write(sheet_row, 6, label=slip_data['Benificiery'])
            worksheet.write(sheet_row, 7, label=slip_data['Currency'])
            worksheet.write(sheet_row, 8, label=slip_data['PO_Amount'])
            worksheet.write(sheet_row, 9, label=slip_data[
                'No_of_Invoice_Received'])
            worksheet.write(
                sheet_row, 10, label=slip_data['Amount_of_Invoices'])
            worksheet.write(sheet_row, 11, label=slip_data['Not_Invoiced'])
            sheet_col += 1
            sheet_row += 1
            last_row = sheet_row

        return worksheet

    @api.model
    def _get_attachment(self, data):
        """
        create and return attachment
        :param data:
        :return:
        """
        today_date = dt.date.today()
        attachment_data = {
            'name': 'Purchase_Order_Status_' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas_fname': 'Purchase_Order_Status_' + str(
                today_date.strftime('%Y-%m-%d')) + '.xls',
            'datas': base64.encodestring(data),
            'res_model': '',
            'res_id': False,
            'mimetype': 'application/vnd.ms-excel'
        }
        attachment_rec = self.env['ir.attachment'].create(attachment_data)
        return attachment_rec


    @api.multi
    def generate_po_status(self):
        """
       Purchase Order Status Report in XLS format
       :return:
       """
        res = self.env['purchase.order']. \
            search([('id', 'in', self._context.get('active_ids')),('state',
                                                                   'not in',
                                                                   ['draft', 'sent'])])
        print"\n\n\nGenerate report", res
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Purchase Order Status Report')
        self.set_header(worksheet)
        po_status_record = self._get_po_records(res)
        self.set_line_data(po_status_record, worksheet)
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        # return data
        attachment_rec = self._get_attachment(data)
        base_url = self.env['ir.config_parameter']. \
            get_param('web.base.url.static')
        download_url = '/web/content/' + str(attachment_rec.id) + '/' + \
                       attachment_rec.name
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "self",
        }
