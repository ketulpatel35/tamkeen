# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
import xlwt, cStringIO, base64
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TaxReport(models.TransientModel):
    _name = 'tax.report.wiz'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        required=True,
        string='Date range'
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    invoice_type = fields.Selection([('customer', 'Invoice'),
                                     ('bill', 'Bill'),
                                     ('both', 'Both')],
                                    'Target', default='both', required=True)
    tax_ids = fields.Many2many('account.tax', 'tax_report_wiz_tax_rel', 
                               'tax_report_wiz_id', 'tax_id', 'Taxes')


    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end
        if self.date_from:
            self.fy_start_date = self.env.user.company_id.find_daterange_fy(
                fields.Date.from_string(self.date_range_id.date_start)
            ).date_start

    @api.multi
    def button_export_xlsx(self):
        inv_line_obj = self.env['account.invoice.line']
        company_currency = self.env.user.company_id.currency_id
        currency_obj = self.env['res.currency']
        for rec in self:
            workbook = xlwt.Workbook()
            sheet_name = 'Tax Report'
            sheet = workbook.add_sheet(sheet_name)
            
            row = 0
            xlwt.add_palette_colour("yellow1", 0x21)
            workbook.set_colour_RGB(0x21, 255,255,153)
            for c in range(0, 6):
                sheet.col(c).width = 256 * 20
            s1 = xlwt.easyxf(
                'align: wrap on, vert centre, horiz center ; font: bold on, italic off;\
                borders: left thin, right thin, top thin, bottom thin;', num_format_str='#,##0.00')
            s2 = xlwt.easyxf(
                'align: wrap on, vert centre, horiz center ;\
                borders: left thin, right thin, top thin, bottom thin;', num_format_str='#,##0.00')
            tax_css = xlwt.easyxf(
                'align: wrap on, vert centre, horiz left ;pattern: pattern solid,fore_colour yellow1;\
                borders: left thin, right thin, top thin, bottom thin;', num_format_str='#,##0.00')
            
            data_css = xlwt.easyxf(
                'align: wrap on', num_format_str='#,##0.00')
            
            sheet.write_merge(0, 1, 0, 3, 'Tax Report', s1)
            
            sheet.write_merge(0, 0, 4, 5, 'Printing Date : %s' % 
                              (datetime.now().\
                               strftime('%d-%B-%Y')), s1)
            sheet.write_merge(1, 1, 4, 5, self.env.user.company_id.name, s1)
            for c in range(0, 2):
                sheet.row(c).height_mismatch = True
                sheet.row(c).height = 256 * 2
    
            row = 2
            col = 0
            sheet.write(row, col, 'Target Data : ', s1)
            col += 1
            old_domain = [('invoice_id.date', '>=', self.date_from),
                      ('invoice_id.date', '<=', self.date_to),
                      ('state', 'in', ('open', 'paid'))]
            if self.invoice_type == 'customer':
                sheet.write(row, col, 'Invoice', s2)
                old_domain += [('invoice_id.type', 'in', ('out_invoice', 'in_refund'))]
            elif self.invoice_type == 'bill':
                sheet.write(row, col, 'Bill', s2)
                old_domain += [('invoice_id.type', 'in', ('in_invoice', 'out_refund'))]
            else:
                sheet.write(row, col, 'Invoice and Bill', s2)
            col += 3
            sheet.write(row, col, 'Date From', s1)
            col += 1
            sheet.write(row, col, 'Date To', s1)
            
            col = 4
            row += 1
            
            sheet.write(row, col, datetime.strptime(self.date_from,
                    DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y'), s2)
            col += 1
            sheet.write(row, col, datetime.strptime(self.date_to,
                    DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%b-%Y'), s2)
            
            col = 0
            row += 1
            sheet.write(row, col, 'Taxes : ', s1)
            col += 1
            sheet.write_merge(row, row, col, col + 2, 
                              self.tax_ids and \
                              ','.join(map(str, [tax.name for tax in self.tax_ids]))\
                              or 'All', s2)
    
            header_lst = ['Tax Name', 'Bill No', 'Partner', 'Invoice Date', 'Accounting Date',
                          'Base Amount', 'Tax Amount',
                          'Base Amount(%s)' % (company_currency.symbol),
                          'Tax Amount(%s)' % (company_currency.symbol)]
            row += 2
            col = 0
            header_row = row
            for header in header_lst:
                sheet.write(row, col, header, s1)
                col += 1
            
            last_column = col - 1
            
            tax_recs = self.tax_ids
            if not tax_recs:
                tax_recs = self.env['account.tax'].search([])
            
            row += 2
            col = 0
            for tax_rec in tax_recs:
                current_row = row
                sheet.write_merge(row, row, col, last_column - 1,
                                  tax_rec.name, tax_css)
                row += 1
                col = 1
                tax_amount = 0.0
                domain = old_domain + [('invoice_line_tax_ids', 'in', tax_rec.id)]
                for inv_line in inv_line_obj.search(domain):
                    inv_currency = inv_line.invoice_id.currency_id
                    sheet.write(row, col, inv_line.invoice_id.number, data_css)
                    col += 1
                    sheet.write(row, col, inv_line.invoice_id.partner_id\
                                and inv_line.invoice_id.partner_id.name\
                                or '', data_css)
                    col += 1
                    sheet.write(row, col, inv_line.date_invoice and
                                datetime.strptime(inv_line.date_invoice,
                                                  DEFAULT_SERVER_DATE_FORMAT)\
                                .strftime('%d-%b-%Y') or '', data_css)
                    col += 1
                    sheet.write(row, col, inv_line.invoice_id.date and
                                datetime.strptime(inv_line.invoice_id.date,
                                                  DEFAULT_SERVER_DATE_FORMAT)\
                                .strftime('%d-%b-%Y') or '', data_css)
                    col += 1
                    sheet.write(row, col, inv_line.price_subtotal, data_css)
                    col += 1
                    sheet.write(row, col, inv_line.price_tax, data_css)
                    col += 1
                    if company_currency.id == inv_currency.id:
                        sheet.write(row, col, inv_line.price_subtotal, data_css)
                        col += 1
                        sheet.write(row, col, inv_line.price_tax, data_css)
                        tax_amount += inv_line.price_tax
                    else:
                        new_subtotal = currency_obj._compute(inv_currency, company_currency,
                                                             inv_line.price_subtotal,
                                                             round=True)
                        sheet.write(row, col, new_subtotal, data_css)
                        col += 1
                        new_tax = currency_obj._compute(inv_currency, company_currency,
                                                        inv_line.price_tax,
                                                        round=True)
                        sheet.write(row, col, new_tax, data_css)
                        tax_amount += new_tax
                    row += 1
                    col = 1
                sheet.write(current_row, last_column, tax_amount, tax_css)
                row += 1
                col = 0
            for c in range(2, row):
                sheet.row(c).height_mismatch = True
                sheet.row(c).height = 450
            sheet.row(header_row).height_mismatch = True
            sheet.row(header_row).height = 550
            stream = cStringIO.StringIO()
            workbook.save(stream)
            attach_id = self.env['tax.report.output.wizard'].create(
                {'name': 'Tax Report.xls',
                 'xls_output': base64.encodestring(stream.getvalue())})
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tax.report.output.wizard',
                'res_id': attach_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new'
            }


class TaxReportOutputWizard(models.TransientModel):
    _name = 'tax.report.output.wizard'
    _description = 'Wizard to store the Excel output'

    xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Trial_Balance.xls')
