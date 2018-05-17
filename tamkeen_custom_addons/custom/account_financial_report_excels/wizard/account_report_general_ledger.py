# -*- coding: utf-8 -*-
from odoo import models, _, api
from odoo.exceptions import UserError

try:
    import xlwt
except ImportError:
    xlwt = None
import cStringIO
import base64


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    _description = "General Ledger Report"

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get(
                'date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        if self._context and self._context.get('excel'):
            return data, records
        return super(AccountReportGeneralLedger, self)._print_report(data)

    def trial_report_excel(self):
        """
        :return:
        """
        data, record = self.with_context({'excel': True}).check_report()
        return self._print_report_excel(data)

    @api.model
    def _get_code(self, data):
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        return codes

    @api.model
    def _get_account_data(self, data):
        """
        get account and account move data for genaral ledger report
        :param data:
        :return:
        """
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        accounts = self.env['account.account']
        if 'active_model' in self.env.context and \
                self.env.context.get('active_model'):
            self.model = self.env.context.get('active_model')
            accounts = self.env[self.model].browse(
                self.env.context.get('active_ids', []))
        else:
            accounts = self.env['account.account'].search([])
        accounts_res = \
            self.env['report.account.report_generalledger'].with_context(
                data['form'].get('used_context', {}))._get_account_move_entry(
                accounts, init_balance, sortby, display_account)
        return accounts_res

    @api.multi
    def _print_report_excel(self, data):
        """
        Trial Balance Excel Report
        :param data:
        :return:
        """
        workbook = xlwt.Workbook()
        s1 = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 450')
        sheet_name = 'General ledger'
        sheet = workbook.add_sheet(sheet_name)
        for c in range(0, 9):
            if c != 1:
                if c == 5:
                    sheet.col(c).width = 256 * 35
                else:
                    sheet.col(c).width = 256 * 20

        title1 = 'General ledger'
        if self.env.user.company_id:
            title1 = self.env.user.company_id.name + ': General ledger'
        sheet.write_merge(0, 3, 0, 9, title1, s1)
        sheet.write_merge(4, 4, 0, 9, '')
        s2 = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal center;')
        s_data = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal center;')
        sheet.write_merge(5, 5, 0, 1, 'Journals', s2)
        code = self._get_code(data)
        sheet.write_merge(6, 6, 0, 1, ', '.join([lt or '' for lt in code]), s2)
        # Display Account
        sheet.write_merge(5, 5, 4, 5, 'Display Account', s2)
        title2 = ''
        display_account = data['form'].get('display_account')
        if display_account == 'all':
            title2 = 'All accounts'
        if display_account == 'movement':
            title2 = 'With movements'
        if display_account == 'not_zero':
            title2 = 'With balance not equal to zero'
        sheet.write_merge(6, 6, 4, 5, title2, s_data)
        # Target Moves
        sheet.write_merge(5, 5, 8, 9, 'Target Moves', s2)
        target_move = data['form'].get('target_move')
        title3 = ''
        if target_move == 'all':
            title3 = 'All Entries'
        if target_move == 'posted':
            title3 = 'All Posted Entries'
        sheet.write_merge(6, 6, 8, 9, title3, s_data)
        # Sorted By
        sheet.write_merge(7, 7, 0, 1, 'Sorted By', s2)
        sortby = data['form'].get('sortby')
        title4 = ''
        if sortby == 'sort_date':
            title4 = 'Date'
        if sortby == 'sort_journal_partner':
            title4 = 'Journal and Partner'
        sheet.write_merge(8, 8, 0, 1, title4, s2)
        date_from = 'Date from'
        if data['form'].get('date_from'):
            date_from = 'Date from : ' + data['form'].get('date_from')
        sheet.write_merge(7, 7, 4, 5, date_from, s2)
        date_to = 'Date to'
        if data['form'].get('date_to'):
            date_from = 'Date from : ' + data['form'].get('date_to')
        sheet.write_merge(8, 8, 4, 5, date_to, s2)

        sheet.write_merge(9, 9, 0, 9, '', s2)

        st_left = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal left;')
        st_right = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal right;')
        s_left = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal left;')
        s_right = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal right;')
        sheet.write(10, 0, 'Date', st_left)
        sheet.write(10, 1, 'JRNL', s2)
        sheet.write(10, 2, 'Partner', s2)
        sheet.write(10, 3, 'Ref', st_left)
        sheet.write(10, 4, 'Move', st_left)
        sheet.write(10, 5, 'Entry Label', st_left)
        currency = ''
        if self.env.user.company_id.currency_id:
            currency = self.env.user.company_id.currency_id.symbol
        tdebit = 'Debit'
        tcredit = 'Credit'
        tbalance = 'Balance'
        if currency != '':
            tdebit = 'Debit' + ' (' + currency + ')'
            tcredit = 'Credit' + ' (' + currency + ')'
            tbalance = 'Balance' + ' (' + currency + ')'
        sheet.write(10, 6, tdebit, st_right)
        sheet.write(10, 7, tcredit, st_right)
        sheet.write(10, 8, tbalance, st_right)
        # sheet.write(10, 9, 'Currency', s2)
        # Genarate Report
        account_data = self._get_account_data(data)
        row_count = 11
        for acc_data in account_data:
            name = acc_data.get('code', '') + acc_data.get('name', '')
            cr = str(acc_data.get('credit', ''))
            sheet.write_merge(row_count, row_count, 0, 5, name, st_left)
            sheet.write(row_count, 6, str(acc_data.get('debit', '')), st_right)
            sheet.write(row_count, 7, cr, st_right)
            sheet.write(row_count, 8, str(acc_data.get('balance', '')),
                        st_right)
            row_count += 1
            for acc_line in acc_data.get('move_lines'):
                sheet.write(row_count, 0, acc_line.get('ldate', ''), s_left)
                sheet.write(row_count, 1, acc_line.get('lcode', ''), s_data)
                sheet.write(row_count, 2, acc_line.get('partner_name', ''),
                            s_data)
                sheet.write(row_count, 3, acc_line.get('lref', ''), s_left)
                sheet.write(row_count, 4, acc_line.get('move_name', ''),
                            s_left)
                sheet.write(row_count, 5, acc_line.get('lname', ''), s_left)
                debit = acc_line.get('debit', '')
                credit = acc_line.get('credit', '')
                balance = acc_line.get('balance', '')
                # if currency != '':
                #     if currency != '':
                #         debit = str(debit) + ' ' + currency
                #         credit = str(credit) + ' ' + currency
                #         balance = str(balance) + ' ' + currency
                sheet.write(row_count, 6, debit, s_right)
                sheet.write(row_count, 7, credit, s_right)
                sheet.write(row_count, 8, balance, s_right)
                row_count += 1
                # sheet.write(row_count, 9, '', s_left)
        stream = cStringIO.StringIO()
        workbook.save(stream)
        attach_id = self.env['accounting.finance.report.output.wizard'].create(
            {'name': 'General ledger.xls',
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
