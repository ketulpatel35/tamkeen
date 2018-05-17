# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT

try:
    import xlwt
except ImportError:
    xlwt = None
import cStringIO
import base64
from datetime import datetime, timedelta


class TrialBalanceReport(models.TransientModel):
    _inherit = "account.balance.report"

    initial_balance = fields.Boolean('Initial Balance')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        if self._context and self._context.get('excel'):
            return data, records
        return super(TrialBalanceReport, self)._print_report(data)

    def trial_report_excel(self):
        data, record = self.with_context({'excel': True}).check_report()
        return self._print_report_excel(data)

    @api.multi
    def _print_report_excel(self, data):
        """
        Trial Balance Excel Report
        :param data:
        :return:
        """
        accounts = False
        if 'active_model' in self.env.context and \
                self.env.context.get('active_model'):
            self.model = self.env.context.get('active_model')
            accounts = self.env[self.model].browse(
                self.env.context.get('active_ids', []))
        else:
            accounts = self.env['account.account'].search([])
        if accounts:
            # accounts = self.env['account.account'].search([])
            display_account = data['form'].get('display_account')

            accounts_dict = \
                self.env['report.account.report_trialbalance'].with_context(
                    data['form'].get('used_context'))._get_accounts(
                    accounts, display_account)

            # Initial Balance
            if self.initial_balance:
                inital_balance_context = dict(data['form'].get('used_context'))
                to_date = data['form'].get('used_context').get('date_from')
                end_date = \
                    datetime.strptime(to_date, '%Y-%m-%d').date() - \
                    timedelta(days=1)
                inital_balance_context['date_from'] = False
                if end_date:
                    inital_balance_context['date_to'] = \
                        end_date.strftime(OE_DATEFORMAT)
                accounts_dict_inital_balance = \
                    self.env[
                        'report.account.report_trialbalance'].with_context(
                        inital_balance_context)._get_accounts(
                        accounts, display_account)

        def get_inital_balance(account, init_balance):
            for acc in init_balance:
                if account.get('name') == acc.get('name') and \
                        account.get('code') == acc.get('code'):
                    return acc.get('balance')
            return 0

        workbook = xlwt.Workbook()
        s1 = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 450')
        sheet_name = 'Trial Balance'
        sheet = workbook.add_sheet(sheet_name)
        for c in range(1, 8):
            sheet.col(c).width = 256 * 20
        title1 = 'Trial Balance'
        if self.env.user.company_id:
            title1 = self.env.user.company_id.name + ': Trial Balance'
        # set title
        sheet.write_merge(0, 2, 0, 7, title1, s1)
        s2 = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal center;')
        s3 = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal center;')
        title2 = ''
        if data['form'].get('display_account') == 'all':
            title2 = 'All accounts'
        if data['form'].get('display_account') == 'movement':
            title2 = 'With movements'
        if data['form'].get('display_account') == 'not_zero':
            title2 = 'With balance not equal to zero'
        if title2:
            sheet.write_merge(3, 3, 0, 1, 'Display Account', s2)
            sheet.write_merge(4, 4, 0, 1, title2, s3)

        if data['form'].get('date_from'):
            df = 'Date from : ' + data['form'].get('date_from')
            sheet.write_merge(3, 3, 2, 4, df, s3)
        if data['form'].get('date_to'):
            dt = 'Date to : ' + data['form'].get('date_to')
            sheet.write_merge(4, 4, 2, 4, dt, s3)
        title3 = ''
        if data['form'].get('target_move') == 'all':
            title3 = 'All Entries'
        if data['form'].get('target_move') == 'posted':
            title3 = 'All Posted Entries'
        if title3:
            sheet.write_merge(3, 3, 5, 6, 'Target Moves', s2)
            sheet.write_merge(4, 4, 5, 6, title3, s3)
        currency = ''
        if self.env.user.company_id.currency_id:
            currency = self.env.user.company_id.currency_id.symbol
        if currency != '':
            sheet.write(3, 7, 'Currency', s2)
            sheet.write(4, 7, currency, s3)

        sheet.write_merge(5, 5, 0, 6, '')
        # Fillup data
        sacc = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal left;')
        sacct = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal left;')
        sdbt = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold 1, italic off, height 200;'
            'alignment: horizontal right;')
        sdb = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 200;'
            'alignment: horizontal right;')
        if accounts_dict:
            sheet.write(6, 0, 'Code', sdbt)
            sheet.write_merge(6, 6, 1, 3, 'Account', sacct)

            # if data['form'].get('include_initial_bal'):
            tdebit = 'Debit'
            tcredit = 'Credit'
            tbalance = 'Balance'
            ibalance = 'Initial Balance'
            if currency != '':
                tdebit = 'Debit' + ' (' + currency + ')'
                tcredit = 'Credit' + ' (' + currency + ')'
                tbalance = 'Balance' + ' (' + currency + ')'
                ibalance = 'Initial Balance' + ' (' + currency + ')'
            col_a = 3
            if self.initial_balance:
                col_a += 1
                sheet.write(6, col_a, ibalance, sdbt)
            col_a += 1
            sheet.write(6, col_a, tdebit, sdbt)
            col_a += 1
            sheet.write(6, col_a, tcredit, sdbt)
            col_a += 1
            sheet.write(6, col_a, tbalance, sdbt)
            # else:
            #     sheet.write(6, 4, 'Debit', sdbt)
            #     sheet.write(6, 5, 'Credit', sdbt)
            #     sheet.write(6, 6, 'Balance', sdbt)
            row_count = 8
            for acc_dict in accounts_dict:
                sheet.write(row_count, 0, acc_dict.get('code'), sdb)
                sheet.write_merge(row_count, row_count, 1, 3,
                                  acc_dict.get('name'), sacc)
                debit = acc_dict.get('debit')
                credit = acc_dict.get('credit')
                # With Initial Balance
                col_count = 3
                balance = acc_dict.get('balance')
                if self.initial_balance:
                    col_count += 1
                    init_bal = \
                        get_inital_balance(acc_dict,
                                           accounts_dict_inital_balance)
                    balance = init_bal + debit - credit
                    sheet.write(row_count, col_count, init_bal, sdb)
                col_count += 1
                sheet.write(row_count, col_count, debit, sdb)
                col_count += 1
                sheet.write(row_count, col_count, credit, sdb)
                col_count += 1
                sheet.write(row_count, col_count, balance, sdb)
                row_count += 1
        # Genarate Report
        stream = cStringIO.StringIO()
        workbook.save(stream)
        attach_id = self.env['accounting.finance.report.output.wizard'].create(
            {'name': 'Financial.xls',
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
