# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
try:
    import xlwt
except ImportError:
    xlwt = None
from odoo import models, api, _
import datetime as dt
import base64
from datetime import datetime, date
from cStringIO import StringIO
from odoo.exceptions import UserError


class PurchaseOrderStatus(models.TransientModel):
    _inherit = 'purchase.order.status.report'
    _description = 'Purchase Orders'

    @api.model
    def set_header(self, worksheet, period_id):
        """
        set header
        :param worksheet: excel sheet object
        :param period_id: object
        :return: updated excel sheet object
        """

        date = period_id
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
            'fore_colour aqua')
        header_0 = "Purchase Order Status Report"
        worksheet.write_merge(0, 0, 0, 15, header_0, s0)

        s1 = xlwt.easyxf(
            'font: bold 1,colour green, height 280;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_back_colour white,'
            'fore_colour white')
        date = period_id
        header_1 = "Last Update : %s " % date
        worksheet.write_merge(1, 1, 0, 11, header_1, s1)

        s2 = xlwt.easyxf(
            'font: bold 1, colour white,height 180;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour light_blue,'
            'fore_colour light_blue')
        header_2 = 'System Invoice Status'
        worksheet.write_merge(1, 1, 12, 13, header_2, s2)

        s3 = xlwt.easyxf(
            'font: bold 1, colour white,height 180;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour light_blue,'
            'fore_colour light_blue')
        header_3 = 'To Be Updated By AP Team'
        worksheet.write_merge(1, 1, 14, 15, header_3, s3)

        s4 = xlwt.easyxf(
            'font: bold 1,height 220, colour white;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour gray50,'
            'fore_colour gray50'
        )
        header_4 = ['PR Number',
                    'PR Creation Date',
                    'Reference',
                    'PO Company Number',
                    # 'Order Date',
                    'PR Approval Date',
                    'PO Approved Date',
                    'Turn Around Time(Days)',
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
            worksheet.write(2, h_12_col, label=h_12, style=s4)
            h_12_col += 1

        s5 = xlwt.easyxf(
            'font: bold 1,height 190, colour white;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour light_blue,'
            'fore_colour light_blue'
        )
        header_5 = [
            'Total of Paid invoices',
            'Total of Non Paid Invoices',
            'Total of Paid invoices',
            'Total of Non Paid Invoices',
        ]
        h_4_col = 15
        for h_4 in header_5:
            worksheet.write(2, h_4_col, label=h_4, style=s5)
            h_4_col += 1
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
            turn_around_time = False
            pr_approval_date = po_approval_date = False
            pr = record_line.requisition_id and record_line.requisition_id.name
            cost_centre_id = record_line.requisition_id and \
                record_line.requisition_id.cost_centre_id and \
                record_line.requisition_id.cost_centre_id.name or 'N/A'
            creation_date = datetime.strptime(record_line.requisition_id.create_date, '%Y-%m-%d %H:%M:%S')

            if record_line.requisition_id.procurement_approval_date or record_line.requisition_id.finance_approval_date:
                pr_approval_date = datetime.strptime(record_line.requisition_id.procurement_approval_date or record_line.requisition_id.finance_approval_date, '%Y-%m-%d %H:%M:%S').date()

            po_approval_date = datetime.strptime(record_line.date_approve, '%Y-%m-%d').date()
            if po_approval_date and pr_approval_date:
                turn_around_time = po_approval_date - pr_approval_date

            data = {
                # 'PR_Number': record_line.partner_ref or 'N/A',
                'PR_Number': pr or 'N/A',
                'PR_Creation_Date': creation_date.date().strftime('%Y-%m-%d'),
                'Reference': record_line.name or 'N/A',
                'PO_Company_Number': record_line.po_company_number or 'N/A',
                # 'Order_Date': record_line.date_order,
                'PR_Approval_Date':pr_approval_date.strftime('%Y-%m-%d') if pr_approval_date else 'N/A',
                'PO_Approved_Date': po_approval_date.strftime('%Y-%m-%d')if po_approval_date else 'Nill',
                'Turn_Around_Time': turn_around_time and turn_around_time.days or 0,
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

            amt_invoice = amt_not_invoice\
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
            total_po_amount += \
                rec.get('PO_Amount') if rec.get('PO_Amount') else 0
            total_no_of_invoice_received += \
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
            worksheet.write(sheet_row, 1, label=slip_data['PR_Creation_Date'])
            worksheet.write(sheet_row, 2, label=slip_data['Reference'])
            worksheet.write(sheet_row, 3, label=slip_data['PO_Company_Number'])
            # worksheet.write(sheet_row, 3, label=slip_data['Order_Date'])
            worksheet.write(sheet_row, 4, label=slip_data['PR_Approval_Date'])
            worksheet.write(sheet_row, 5, label=slip_data['PO_Approved_Date'])
            worksheet.write(sheet_row, 6, label=slip_data['Turn_Around_Time'])
            worksheet.write(sheet_row, 7, label=slip_data['Supplier'])
            worksheet.write(sheet_row, 8, label=slip_data['Cost_Center'])
            worksheet.write(sheet_row, 9, label=slip_data['Benificiery'])
            worksheet.write(sheet_row, 10, label=slip_data['Currency'])
            worksheet.write(sheet_row, 11, label=slip_data['PO_Amount'])
            worksheet.write(sheet_row, 12, label=slip_data[
                            'No_of_Invoice_Received'])
            worksheet.write(
                sheet_row, 13, label=slip_data['Amount_of_Invoices'])
            worksheet.write(sheet_row, 14, label=slip_data['Not_Invoiced'])
            worksheet.write(sheet_row, 15, label=slip_data['Paid_invoices'],
                            style=s4)
            worksheet.write(
                sheet_row, 16, label=slip_data['Non_Paid_Invoices'], style=s4)
            worksheet.write(sheet_row, 17, label=slip_data[
                            'default_Paid_invoices'], style=s4)
            worksheet.write(sheet_row, 18, label=slip_data[
                            'default_Non_Paid_Invoices'], style=s4)
            sheet_col += 1
            sheet_row += 1
            last_row = sheet_row

        worksheet.row(last_row).height = 500
        s6 = xlwt.easyxf(
            'font: bold 1,height 180;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'alignment: horizontal center;'
            'pattern: pattern solid, pattern_back_colour white,'
            'fore_colour white')
        header_6 = 'Total'

        worksheet.write_merge(last_row, last_row, 0, 10, header_6, s6)
        worksheet.write(last_row, 11, label=total.get('total_po_amount'))
        worksheet.write(last_row, 12, label=total.get(
            'total_no_of_invoice_received'))
        worksheet.write(last_row, 13, label=total.get(
            'total_amount_of_invoices'))
        worksheet.write(last_row, 14, label=total.get('total_not_invoiced'))
        worksheet.write(last_row, 15, label=total.get(
            'default_total_of_paid_invoices'))
        worksheet.write(last_row, 16, label=total.get(
            'default_total_of_non_paid_invoices'))
        worksheet.write(last_row, 17, label=total.get('total_of_paid_invoices'))
        worksheet.write(last_row, 18, label=total.get(
            'total_of_non_paid_invoices'))
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
    def print_report(self):
        """
        Purchase Order Status Report in XLS format
        :return:
        """
        if self.partner_id:
            res = self.env['purchase.order'].\
                search([('partner_id', '=', self.partner_id.id),
                        ('date_approve', '>=', self.date_from),
                        ('date_approve', '<=', self.date_to),
                        ('state', 'not in', ['draft', 'sent'])])
        else:
            res = self.env['purchase.order'].\
                search([('date_approve', '>=', self.date_from),
                        ('date_approve', '<=', self.date_to),
                        ('state', 'not in', ['draft', 'sent'])])
        if not res:
            raise UserError(_('No Records Found For this Criteria'))
        # if res:
        #     for rec in res:
        #         if self.date_to and rec.date_approve <= self.date_to:
        #             record.append(rec)
        #         else:
        #             record.append(rec)
        # else:
        #     raise UserError(_('No Records Found For this Criteria'))

        period_id = datetime.now().date()
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Purchase Order Status Report')
        self.set_header(worksheet, period_id)
        po_status_record = self._get_po_records(res)
        self.set_line_data(po_status_record, worksheet)
        # # Freeze column,row
        # worksheet.set_panes_frozen(True)
        # worksheet.set_horz_split_pos(5)
        # worksheet.set_vert_split_pos(8)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        # return data
        attachment_rec = self._get_attachment(data)
        # save to particular path
        # workbook.save('/home/bista/Desktop/ABCD.xls')
        base_url = self.env['ir.config_parameter'].\
            get_param('web.base.url.static')
        download_url = '/web/content/' + str(attachment_rec.id) + '/' + \
                       attachment_rec.name
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "self",
        }
