# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
try:
    import xlwt
except ImportError:
    xlwt = None
import cStringIO
import base64


class AccountPartnerStatement(models.TransientModel):
    _name = "wizard.account.partner.statement"

    @api.onchange('statement_type')
    def onchange_statement_type(self):
        domain = False
        if not self.statement_type:
            return
        self.partner_id = False
        if self.statement_type == 'customer':
            domain = [('customer', '=', True)]
        if self.statement_type == 'vendor':
            domain = [('supplier', '=', True)]
        if self.statement_type == 'both':
            domain = []
        return {'domain': {'partner_id': domain}}

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    statement_type = fields.Selection([('customer', 'Customer'),
                                       ('vendor', 'Vendor'),
                                       ('both', 'Customer/Vendor')], string="Satement")
    partner_id = fields.Many2one('res.partner', string="Partner")
    invoice_type = fields.Selection([('all_invoice', 'All Invoice'),
                                     ('open', 'Open Invoice')], string="Invoice")
    include_analytic_account = fields.Boolean(
        string="Include Analytic Account ?")

    @api.model
    def _set_header(self, sheet):
        """
        set header
        :param sheet: sheet object
        :return:
        """
        sheet.col(1).width = 256 * 10

        style1 = xlwt.easyxf('align: horiz centre ; font: name Arial,'
                             'bold on, italic off, height 320;'
                             'borders: left thin, right thin, top thin, bottom thin;')
        style2 = xlwt.easyxf('align: horiz centre; font: name Arial,'
                             'bold on, height 160;'
                             'borders: left thin, right thin, top thin, bottom thin;'
                             'pattern:  pattern solid, fore_colour gray25;')
        style3 = xlwt.easyxf('align: horiz centre; font: name Arial,'
                             'bold on, height 160;'
                             'borders: left thin, right thin, top thin, bottom thin;')
        style4 = xlwt.easyxf('align: horiz centre; font: name Arial;'
                             'borders: left thin, right thin, top thin, bottom thin;')

        title = sub_title = sub_header = ''
        if self.statement_type == 'customer':
            title = 'Customer Statement of Account'
            sub_title = 'Customer Information'
            sub_header = 'Customer Name:'
        elif self.statement_type == 'vendor':
            title = 'Vendor Statement of Account'
            sub_title = 'Vendor Information'
            sub_header = 'Vendor Name:'
        else:
            title = 'Customer/Vendor Statement of Account'
            sub_title = 'Customer/Vendor Information'
            sub_header = 'Customer/Vendor Name:'

        sheet.write_merge(0, 2, 0, 8, title, style1)
        sheet.write_merge(3, 3, 0, 8, '')
        sheet.write_merge(4, 4, 0, 8, sub_title, style2)

        sheet.write_merge(5, 5, 0, 3, 'Printed Date:', style3)
        sheet.write_merge(5, 5, 4, 8, date.today(), style4)

        sheet.write_merge(6, 6, 0, 3, 'Statement Date:', style3)
        sheet.write_merge(6, 6, 4, 8, self.start_date + ' ' + 'TO' + ' ' + self.end_date, style4)

        sheet.write_merge(7, 7, 0, 3, sub_header, style3)
        sheet.write_merge(7, 7, 4, 8, self.partner_id.name, style4)

        sheet.write_merge(8, 8, 0, 8, '')
        sheet.set_panes_frozen(True)
        return sheet

    @api.model
    def _set_line_header(self, sheet):
        """
        set line header
        :param sheet: sheet object
        :return:
        """
        headers = ['sr_no', 'date', 'entry', 'label', 'ref', 'po',
                   'analytic_account', 'debit', 'credit', 'balance']
        
        po = ref = ''
        if self.statement_type == 'customer':
            po = 'SO/Origin'
            ref = 'Customer Ref.'
        elif self.statement_type == 'vendor':
            po = 'PO/Origin'
            ref = 'Vendor Ref.'
        else:
            po = 'SO/PO/Origin'
            ref = 'Customer/Vendor Ref.'

        header_title = {'sr_no': "Sr.No", 'date': "Date", 'entry': "Entry",
                        'label': "Label", 'ref': ref, 'po': po,
                        'analytic_account': "CC/Analytic Account",
                        'debit': "Debit", 'credit': "Credit", 'balance': "Balance"}
        style = xlwt.easyxf('align: horiz centre; font: name Arial,'
                            'bold on, height 160;'
                            'borders: left thin, right thin, top thin, bottom thin;'
                            'pattern:  pattern solid, fore_colour gray25;')
        style2 = xlwt.easyxf('align: horiz centre; font: name Arial,'
                             'bold on, height 160;'
                             'borders: left thin, right thin, top thin, bottom thin;')

        sheet.write_merge(9, 9, 0, 5, 'Opening Balance:', style)
        opening_balance = self._sum_partner(self.partner_id, 'debit - credit')
        sheet.write_merge(9, 9, 6, 8, opening_balance, style2)

        # Set Line headers
        column_counter = 0
        if not self.include_analytic_account:
            headers.remove('analytic_account')
            del header_title['analytic_account']
        for header in headers:
            if header in ['ref', 'analytic_account']:
                sheet.col(column_counter).width = 256 * 20
            sheet.write(10, column_counter, header_title.get(header), style)
            column_counter += 1

    @api.model
    def get_accounts(self):
        ACCOUNT_TYPE = []
        if self.statement_type == 'vendor':
            ACCOUNT_TYPE = ['payable']
        elif self.statement_type == 'customer':
            ACCOUNT_TYPE = ['receivable']
        else:
            ACCOUNT_TYPE = ['payable', 'receivable']
        self.env.cr.execute("""
                    SELECT a.id
                    FROM account_account a
                    WHERE a.internal_type IN %s
                    AND NOT a.deprecated""",
                            (tuple(ACCOUNT_TYPE),))
        return [a for (a,) in self.env.cr.fetchall()]

    @api.model
    def _set_line_footer(self, sheet, data, workbook, partner_rec):
        row_count = data.get('row_count')
        """
        set line Footer
        :param sheet: sheet object
        :return: sheet object
        """
        style_footer = xlwt.easyxf('align: horiz centre; font: name Arial,'
                                   'bold on, height 160;'
                                   'borders: left thin, right thin, top thin, bottom thin;'
                                   'pattern:  pattern solid, fore_colour gray25;')
        style2 = xlwt.easyxf('align: horiz right; font: name Arial,'
                             'bold on, height 160;'
                             'borders: left thin, right thin, top thin, bottom thin;'
                             'pattern:  pattern solid, fore_colour gray25;')
        total_of_partner = 'Total of Partner (' + partner_rec.name + '):'
        col = 5
        if self.include_analytic_account:
            sheet.write_merge(row_count, row_count, 0, 9, '')
            col += 1
        else:
            sheet.write_merge(row_count, row_count, 0, 8, '')
        row_count += 1
        sheet.write_merge(row_count, row_count, 0, col, total_of_partner, style_footer)
        sheet.write(row_count, col + 1, data.get('total_debit'), style2)
        sheet.write(row_count, col + 2, data.get('total_credit'), style2)
        sheet.write(row_count, col + 3, data.get('balance'), style2)

    @api.model
    def _sum_partner(self, partner, field):
        account_ids = self.get_accounts()
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context({'date_from': self.start_date,
                                                                     'initial_bal': True,
                                                                     'strict_range': True})._query_get()
        params = [partner.id, tuple(account_ids)] + query_get_data[2]
        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND account_id IN %s
                    AND """ + query_get_data[1]
        self.env.cr.execute(query, tuple(params))
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.multi
    def get_lines(self):
        account_ids = self.get_accounts()
        lang_id = self.env['res.lang']._lang_get(self.env.context.get('lang') or 'en_US')

        date_format = lang_id.date_format
        start_date = datetime.strptime(self.start_date,
                                       DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
        end_date = datetime.strptime(self.end_date,
                                     DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
        partner_id = self.partner_id
        
        query = """SELECT aml.id, aml.date, aml.ref, aml.name,
                   aml.debit, aml.credit, aml.invoice_id,res.account_invoice_id
                   FROM account_move_line aml
                   LEFT JOIN account_move am ON am.id = aml.move_id
                   LEFT JOIN account_account ac ON ac.id = aml.account_id
                   LEFT JOIN account_invoice ai oN ai.id = aml.invoice_id
                   LEFT JOIN account_invoice_account_move_line_rel res ON res.account_move_line_id=aml.id
                   where aml.date >= '%s' AND
                   aml.date <= '%s' AND
                   aml.partner_id = '%s' AND
                   aml.account_id IN %s
                """ % (start_date, end_date, str(partner_id.id), tuple(account_ids))
        if self.invoice_type == 'all_invoice':
            query += """AND 
                        CASE
                            WHEN aml.invoice_id is not null THEN ai.state IN ('open','paid')
                        ELSE
                            aml.id=res.account_move_line_id and res.account_invoice_id in (select id from account_invoice where state IN ('open','paid'))
                        END
                        ORDER BY aml.id """
        else:
            query += """AND
                        CASE
                            WHEN aml.invoice_id is not null THEN ai.state = 'open'
                        ELSE
                            aml.id=res.account_move_line_id and res.account_invoice_id in (select id from account_invoice where state = 'open')
                        END
                        ORDER BY aml.id """
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        return res

    @api.model
    def _set_data(self, sheet):
        """
        :param sheet: sheet object
        :return:
        """
        style = xlwt.easyxf('align: horiz centre; font: name Arial;'
                             'borders: left thin, right thin, top thin, bottom thin;')
        style2 = xlwt.easyxf('align: horiz left; font: name Arial;'
                             'borders: left thin, right thin, top thin, bottom thin;')
        style3 = xlwt.easyxf('align: horiz right; font: name Arial;'
                             'borders: left thin, right thin, top thin, bottom thin;')
        sr_no = 1
        count = 11
        invoice_obj = self.env['account.invoice']
        account_move_line_obj = self.env['account.move.line']
        total_credit = total_debit = balance = 0.00
        opening_balance = self._sum_partner(self.partner_id, 'debit - credit')
        for line in self.get_lines():
            col = 6
            invoice_id = invoice_obj.browse(line.get('invoice_id'))
            if not invoice_id:
                invoice_id = invoice_obj.browse(line.get('account_invoice_id'))
            move_line_id = account_move_line_obj.browse(line.get('id'))
            sheet.write(count, 0, sr_no, style)
            sheet.write(count, 1, line.get('date'), style)
            sheet.write(count, 2, move_line_id.move_id.name or '', style2)
            sheet.write(count, 3, line.get('name') or '', style2)
            sheet.write(count, 4, invoice_id.name or invoice_id.origin or invoice_id.reference or '', style2)
            sheet.write(count, 5, invoice_id.origin or '', style2)
            if self.include_analytic_account:
                sheet.write(count, col, move_line_id.analytic_account_id.name or '', style2)
                col += 1
            sheet.write(count, col, line.get('debit'), style3)
            sheet.write(count, col + 1, line.get('credit'), style3)
            balance = (line.get('debit') - line.get('credit')) + opening_balance
            sheet.write(count, col + 2, balance, style3)
            opening_balance = balance
            count += 1
            sr_no += 1
            total_credit += line.get('credit') or 0.00
            total_debit += line.get('debit') or 0.00
        result = {'row_count': count, 'total_debit': float(total_debit), 'total_credit': float(total_credit), 'balance': balance or opening_balance}
        return result

    @api.multi
    def print_xls_report(self):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Accounting Statement Report')
        sheet = self._set_header(sheet)
        self._set_line_header(sheet)
        data = self._set_data(sheet)
        self._set_line_footer(sheet, data , workbook, self.partner_id)
        stream = cStringIO.StringIO()
        workbook.save(stream)
        name = ''
        if self.statement_type == 'customer':
            name = 'Customer Statement'
        elif self.statement_type == 'vendor':
            name = 'Vendor Statement'
        else:
            name = 'Customer/Vendor Statement'
        attach_id = self.env['accounting.finance.report.output.wizard'].create(
            {'name': name + '.xls',
             'xls_output': base64.encodestring(stream.getvalue())})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'accounting.finance.report.output.wizard',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
