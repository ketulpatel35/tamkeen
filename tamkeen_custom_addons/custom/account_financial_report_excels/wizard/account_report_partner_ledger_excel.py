# -*- coding: utf-8 -*-
from odoo import models, api

try:
    import xlwt
except ImportError:
    xlwt = None
import cStringIO
import base64
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    _description = "Account Partner Ledger"

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency})
        if self._context and self._context.get('excel'):
            return data
        return self.env['report'].get_action(self,
                                             'account.report_partnerledger',
                                             data=data)

    def trial_report_excel(self):
        data = self.with_context({'excel': True}).check_report()
        return self._print_report_excel(data)

    @api.model
    def _set_header(self, sheet, company_name, currency, data, workbook):
        """
        set excel report header
        :param sheet: excel sheet object
        :param company_name: company name
        :param currency: currency
        :return: sheet object
        """
        sheet.col(1).width = 256 * 20
        sheet.col(3).width = 256 * 25
        sheet.col(4).width = 256 * 40
        sheet.col(5).width = 256 * 20
        sheet.col(6).width = 256 * 20
        sheet.col(7).width = 256 * 20

        # first Header Set
        header1 = 'PARTNER LEDGER'
        if company_name:
            header1 = 'PARTNER LEDGER - ' + company_name
            if currency:
                header1 = 'PARTNER LEDGER - ' + company_name + ' - ' + currency
        style1 = xlwt.easyxf('align: horiz left ; font: name Times New Roman,'
                             'bold off, italic off, height 450')
        sheet.write_merge(0, 2, 0, 7, header1, style1)
        # set blank line
        sheet.write_merge(3, 3, 0, 7, '')
        xlwt.add_palette_colour("c_colour", 0x16)
        workbook.set_colour_RGB(0x16, 153, 255, 255)
        style2 = xlwt.easyxf(
            'align: horiz left; font: name Times New Roman,'
            'bold 1, italic off, height 200;'
            'alignment: horizontal center;'
            'pattern: pattern solid, fore_colour c_colour;')
        style3 = xlwt.easyxf(
            'align: horiz left; font: name Times New Roman,'
            'bold off, italic off, height 200;'
            'alignment: horizontal center;')
        sheet.write_merge(4, 4, 0, 2, 'Periods Filter', style2)
        d_from = data['form'].get('date_from')
        d_to = data['form'].get('date_to')
        if d_from and d_to:
            sheet.write_merge(5, 5, 0, 2, 'From: %s - %s' % (d_from, d_to),
                              style3)
        else:
            sheet.write_merge(5, 5, 0, 2, '')
        sheet.write_merge(4, 4, 3, 4, 'Accounts Filter', style2)
        sheet.write_merge(5, 5, 3, 4, 'Accounts Filter', style3)
        sheet.write_merge(4, 4, 5, 7, 'Target Moves', style2)
        target_move = ''
        if data['form'].get('target_move') == 'all':
            target_move = 'All Entries'
        if data['form'].get('target_move') == 'posted':
            target_move = 'All Posted Entries'
        sheet.write_merge(5, 5, 5, 7, target_move, style3)
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(7)
        return sheet

    @api.model
    def _set_line_header(self, sheet, data, row_count, workbook):
        """
        set line header
        :param sheet: sheet object
        :param data: dictonary
        :return:
        """
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 255, 204)
        style_title = xlwt.easyxf('pattern: pattern solid, fore_colour '
                                  'custom_colour;'
                                  'align: horiz left; font: bold 1, height '
                                  '200;')
        sheet.write(row_count, 0, 'Date', style_title)
        sheet.write(row_count, 1, 'Entry', style_title)
        sheet.write(row_count, 2, 'Journal', style_title)
        sheet.write(row_count, 3, 'Partner', style_title)
        sheet.write(row_count, 4, 'Label', style_title)
        sheet.write(row_count, 5, 'Debit', style_title)
        sheet.write(row_count, 6, 'Credit', style_title)
        sheet.write(row_count, 7, 'Cumul. Bal.', style_title)

    @api.model
    def _set_line_footer(self, sheet, data, row_count, workbook, partner_rec):
        """
        set line Footer
        :param sheet: sheet object
        :param data: dictonary
        :return: sheet object
        """
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 255, 255, 204)
        style_footer = xlwt.easyxf('pattern: pattern solid, '
                                   'fore_colour custom_colour;'
                                   'align: horiz right; font: '
                                   'bold 1, height 200;')
        sheet.write_merge(row_count, row_count, 0, 4, 'Cumulated balance on '
                                                      'Partner', style_footer)
        partner_debit = self._sum_partner(data, partner_rec, 'debit')
        partner_credit = self._sum_partner(data, partner_rec, 'credit')
        partner_balance = self._sum_partner(data, partner_rec,
                                            'debit - credit')
        sheet.write(row_count, 5, partner_debit, style_footer)
        sheet.write(row_count, 6, partner_credit, style_footer)
        sheet.write(row_count, 7, partner_balance, style_footer)

    @api.model
    def _lines(self, data, partner):
        full_account = []
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '
        params = [partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """
            SELECT "account_move_line".id, "account_move_line".date,
            j.code, acc.code as a_code, acc.name as a_name,
            "account_move_line".ref, m.name as move_name,
            "account_move_line".name, "account_move_line".debit,
            "account_move_line".credit,
            "account_move_line".amount_currency,
            "account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON
            ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON
            ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            WHERE "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + \
                query_get_data[1] + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            r['date'] = datetime.strptime(r['date'],
                                          DEFAULT_SERVER_DATE_FORMAT).strftime(
                date_format)
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            full_account.append(r)
        return full_account

    @api.model
    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '

        params = [partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def get_partner_ladger_data(self, data):
        """
        :param data:
        :return:
        """
        data['computed'] = {}
        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
                    SELECT a.id
                    FROM account_account a
                    WHERE a.internal_type IN %s
                    AND NOT a.deprecated""",
                            (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in
                                           self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '
        query = """
                    SELECT DISTINCT "account_move_line".partner_id
                    FROM """ + query_get_data[0] + """, account_account AS
                    account, account_move AS am
                    WHERE "account_move_line".partner_id IS NOT NULL
                        AND "account_move_line".account_id = account.id
                        AND am.id = "account_move_line".move_id
                        AND am.state IN %s
                        AND "account_move_line".account_id IN %s
                        AND NOT account.deprecated
                        AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in
                       self.env.cr.dictfetchall()]
        if self.partner_ids:
            partner_ids = set(partner_ids) & set(self.partner_ids.ids)

        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref, x.name))
        docargs = {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'partners': partners,
            'time': time,
        }
        return docargs

    @api.model
    def _set_data(self, sheet, data, row_count, workbook, partner_rec):
        """
        :param sheet: sheet object
        :param data: data dictonary
        :param row_count: counter
        :param workbook: sheer object
        :param partner_rec: partner record
        :return:
        """
        count = row_count
        for line in self._lines(data, partner_rec):
            sheet.write(count, 0, line['date'])
            sheet.write(count, 1, line['move_name'])
            sheet.write(count, 2, line['code'])
            sheet.write(count, 3, partner_rec.name)
            sheet.write(count, 4, line['name'])
            sheet.write(count, 5, line['debit'])
            sheet.write(count, 6, line['credit'])
            sheet.write(count, 7, line['progress'])
            count += 1
        return count

    @api.multi
    def _print_report_excel(self, data):
        """
        Trial Balance Excel Report
        :param data:
        :return:
        """
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Account Partner Ledger')

        # set first header
        company_name = ''
        currency = ''
        if self.env.user.company_id:
            company_name = self.env.user.company_id.name
        if self.env.user.company_id.currency_id:
            currency = self.env.user.company_id.currency_id.symbol
        docargs = self.get_partner_ladger_data(data)
        sheet = self._set_header(sheet, company_name, currency, data, workbook)
        sheet.write_merge(6, 6, 0, 7, '')
        row_count = 7
        style_ht = xlwt.easyxf('align: horiz left; font: bold 1, height 220;')
        for partner_rec in docargs.get('partners'):
            sheet.write_merge(row_count, row_count, 0, 7, partner_rec.name,
                              style_ht)
            row_count += 1
            self._set_line_header(sheet, data, row_count, workbook)
            row_count += 1
            row_count = self._set_data(sheet, data, row_count, workbook,
                                       partner_rec)
            self._set_line_footer(sheet, data, row_count, workbook,
                                  partner_rec)
            row_count += 3
        # Genarate Report
        stream = cStringIO.StringIO()
        workbook.save(stream)
        attach_id = self.env['accounting.finance.report.output.wizard'].create(
            {'name': 'Account Partner Ledger.xls',
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
