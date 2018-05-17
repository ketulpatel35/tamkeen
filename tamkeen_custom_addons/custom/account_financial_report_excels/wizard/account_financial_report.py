# -*- coding: utf-8 -*-
import xlwt
import cStringIO
import base64
import datetime
from openerp import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from datetime import datetime, timedelta


class FinanceAccountingReport(models.TransientModel):
    _inherit = "accounting.report"
    show_inital_balance = fields.Boolean('Initial Balance')

    @api.multi
    def check_report_excel(self):
        res = super(FinanceAccountingReport, self).check_report()
        return self._print_report_excel(res)

    @api.multi
    def _print_report_excel(self, data):
        workbook = xlwt.Workbook()
        title_style_comp_left = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,\
            bold off, italic off, height 450')
        title_style1_table_head = xlwt.easyxf(
            'font: name Times New Roman,bold on, italic off,\
             height 200; borders: top double, bottom double, left \
             double, right double;')
        title_style1_table_headbal = xlwt.easyxf('align: horiz right ;'
                                                 'font: name Times New Roman,'
                                                 'bold on, italic off,'
                                                 'height 200; borders: '
                                                 'top double, bottom double,'
                                                 'left double, right double;')
        title_style1_table_head_bold = xlwt.easyxf(
            'align: horiz right ;font: name Times New Roman,bold on,'
            'italic off, height 200;')
        title_style1_table_head1 = xlwt.easyxf('font: name Times New Roman,'
                                               'bold on, italic off,'
                                               'height 200')
        title_style1_table_normal = xlwt.easyxf('font: name Times New Roman,'
                                                'bold off, italic off,'
                                                'height 200')
        title_style1_table_normal_right = xlwt.easyxf('align: horiz right ;'
                                                      'font: name Times New '
                                                      'Roman,bold off, '
                                                      'italic off, height 200')
        title_style1_table_data_sub = xlwt.easyxf('font: name Times New Roman,'
                                                  'bold off, italic off, '
                                                  'height 190')

        financial_report_obj = self.env['report.account.report_financial']
        get_account_lines = financial_report_obj.get_account_lines(
            data['data']['form'])
        from_date = self.date_from or None
        date_to = self.date_to or None
        to_date = self.date_from
        show_inital_balance = from_date and True or False
        check_inial_balace = self.read(['show_inital_balance'])
        show_inital_balance = show_inital_balance and check_inial_balace and \
            check_inial_balace[0].get(
                'show_inital_balance') or False
        end_date = False
        if from_date:
            end_date = \
                datetime.strptime(from_date, '%Y-%m-%d').date() - timedelta(
                    days=1)

        new_context_data = dict(data['data']['form'])
        new_context_data['date_from'] = False
        new_context_data['used_context']['date_from'] = False

        if end_date:
            new_context_data['date_to'] = \
                end_date.strftime(OE_DATEFORMAT)
            new_context_data['used_context']['date_to'] = \
                end_date.strftime(OE_DATEFORMAT)

        get_account_lines_header_data = \
            financial_report_obj.get_account_lines(new_context_data)
        # For ---------------------- All Account -------------------
        all_context_data = dict(data['data']['form'])
        all_context_data['date_from'] = False
        all_context_data['used_context']['date_from'] = False
        # _to_date = data['data']['form'].get('used_context').get('date_to')
        _end_date = None
        if date_to:
            _end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        if _end_date:
            all_context_data['date_to'] = \
                _end_date.strftime(OE_DATEFORMAT)
            all_context_data['used_context']['date_to'] = \
                _end_date.strftime(OE_DATEFORMAT)

        all_account_lines_header_data = \
            financial_report_obj.get_account_lines(new_context_data)

        # This have some issues - have to look into the balances-
        # Inital Balnce from prev year
        def get_inital_balance_header(header_line, init_balance):
            for line in init_balance:
                if line.get('level') != 0:
                    if line.get('level') < 3:
                        if header_line['name'] == line['name']:
                            return line['balance']
            return 0

        def check_in_current_year(all_line, current_year_line, pre_year_line):
            for line in current_year_line:
                if line.get('level') != 0:
                    if line['name'] == all_line['name']:
                        return line
            for p_line in pre_year_line:
                if p_line.get('level') != 0:
                    if p_line['name'] == all_line['name']:
                        p_line = dict(p_line)
                        p_line.update({
                            'pline': True,
                            'credit': 0.00,
                            'debit': 0.00,
                        })
                        return p_line
            return {}

        def get_inital_balance_parser(current_line, account_data):
            sum_value = 0.0
            for line in account_data:
                if line.get('level') != 0:
                    if line.get('level') < 3:
                        if current_line['name'] == line['name']:
                            return line['balance']

            return sum_value

        def _get_inital_bal_sheet(data, to_date=None):
            qry = """
            with temp_bal_sheet as (
            select account_id as account_id,
            acc.code||' '||acc.name as account_name,
            sum(balance) as balance from account_move_line mvl
            left join account_move mv ON (mvl.move_id = mv.id)
            left join account_account acc ON (mvl.account_id = acc.id)
            """
            qry_params = (
                data['name'],
            )

            if to_date:
                qry_params = (
                    to_date,
                    data['name'],
                )
                qry += """
                 where mvl.date < %s
                 """
            if self.target_move == 'posted':
                qry += """
                 and mv.state = 'posted'
                 """

            qry += """
            group by account_id,acc.code,acc.name
            )
            select balance from temp_bal_sheet where account_name = %s
            """

            self.env.cr.execute(qry, qry_params)
            res = self.env.cr.dictfetchone()
            init_bal = res and res['balance'] or 0.0
            end_bal = init_bal + data['debit'] - data['credit']
            return init_bal, end_bal

        sheet_name = 'Financial'
        sheet = workbook.add_sheet(sheet_name)
        comp_id = self.env.user.company_id
        # currency_id = comp_id.currency_id
        sheet.write_merge(
            0,
            1,
            0,
            3,
            self.account_report_id.name,
            title_style_comp_left)
        sheet.write(
            0,
            5,
            'Printing Date: ' +
            datetime.now().strftime('%Y-%m-%d'),
            title_style1_table_head1)
        sheet.write(1, 5, comp_id.name, title_style1_table_head1)

        if self.date_from:
            sheet.write(3, 2, 'Date from :', title_style1_table_head1)
            sheet.write(4, 2, self.date_from, title_style1_table_data_sub)
        if self.date_to:
            sheet.write(3, 3, 'Date To :', title_style1_table_head1)
            sheet.write(4, 3, self.date_to, title_style1_table_data_sub)

        sheet.write(3, 0, 'Target Moves :', title_style1_table_head1)
        if self.target_move == 'all':
            sheet.col(0).width = 256 * 40
            sheet.col(1).width = 256 * 18
            sheet.col(2).width = 256 * 18
            sheet.col(3).width = 256 * 18
            sheet.write(4, 0, 'All Entries', title_style1_table_data_sub)
        if self.target_move == 'posted':
            sheet.col(0).width = 256 * 40
            sheet.col(1).width = 256 * 18
            sheet.col(2).width = 256 * 18
            sheet.col(3).width = 256 * 18
            column = sheet.col(8)
            column.width = 256 * 18
            sheet.write(4, 0, 'All Posted Entries',
                        title_style1_table_data_sub)

        if self.debit_credit:
            col = 0
            sheet.write(8, 0, 'Name', title_style1_table_head)
            if show_inital_balance:
                col += 1
                sheet.write(8, col, 'Inital', title_style1_table_headbal)
            col += 1
            sheet.write(8, col, 'Debit', title_style1_table_headbal)
            col += 1
            sheet.write(8, col, 'Credit', title_style1_table_headbal)
            col += 1
            sheet.write(8, col, 'Balance', title_style1_table_headbal)

            row_data = 9
            for all_line in all_account_lines_header_data:
                line = {}

                if all_line.get('level') != 0:
                    line = check_in_current_year(all_line,
                                                 get_account_lines,
                                                 get_account_lines_header_data)
                if line:
                    if line.get('level') != 0:
                        if line.get('level') < 3:
                            # Initial
                            # inital_balance = 0
                            col_1 = 0
                            sheet.write(
                                row_data, col_1, str(line['name']),
                                title_style1_table_head1)
                            inital_balance = 0.00
                            if show_inital_balance:
                                col_1 += 1
                                if line.get('name') and line.get('name') == \
                                        'Profit and Loss.':
                                    inital_balance = 0.00
                                elif 'p_line' in line and line.get('p_line'):
                                    inital_balance = line.get('balance')
                                else:
                                    inital_balance = get_inital_balance_header(
                                        line, get_account_lines_header_data)

                                sheet.write(
                                    row_data, col_1, inital_balance,
                                    title_style1_table_head_bold)
                            col_1 += 1
                            sheet.write(
                                row_data, col_1, line['debit'],
                                title_style1_table_head_bold)
                            col_1 += 1
                            sheet.write(
                                row_data, col_1, line['credit'],
                                title_style1_table_head_bold)
                            col_1 += 1
                            balance_header = inital_balance + line['debit'] \
                                - line['credit']
                            sheet.write(
                                row_data, col_1, balance_header,
                                title_style1_table_head_bold)
                        else:
                            # Initial Balance
                            if show_inital_balance:
                                inital_balance, ending_balance = \
                                    _get_inital_bal_sheet(line, to_date)
                            else:
                                inital_balance, ending_balance = 0.0, line[
                                    'balance']

                            col_2 = 0
                            sheet.write(
                                row_data, col_2, '    ' + str(
                                    line['name']), title_style1_table_normal)
                            if show_inital_balance:
                                col_2 += 1
                                sheet.write(
                                    row_data, col_2, inital_balance,
                                    title_style1_table_normal_right)
                            col_2 += 1
                            sheet.write(
                                row_data, col_2,
                                line['debit'],
                                title_style1_table_normal_right)
                            col_2 += 1
                            sheet.write(
                                row_data, col_2,
                                line['credit'],
                                title_style1_table_normal_right)
                            col_2 += 1
                            sheet.write(
                                row_data, col_2,
                                ending_balance,
                                title_style1_table_normal_right)
                        row_data += 1
        if not self.debit_credit and not self.enable_filter:
            sheet.write(8, 0, 'Name', title_style1_table_head)
            sheet.write(8, 1, 'Balance', title_style1_table_headbal)

            row_data = 9
            for line in get_account_lines:
                if line.get('level') != 0:
                    if line.get('level') < 3:
                        sheet.write(
                            row_data, 0, str(
                                line['name']), title_style1_table_head1)
                        sheet.write(
                            row_data, 1, line['balance'],
                            title_style1_table_head_bold)
                    else:
                        sheet.write(row_data, 0, '    ' + str(
                            line['name']), title_style1_table_normal)
                        sheet.write(
                            row_data, 1, line['balance'],
                            title_style1_table_normal_right)
                    row_data += 1
        if not self.debit_credit and self.enable_filter:
            sheet.write(8, 0, 'Name', title_style1_table_head)
            sheet.write(8, 1, 'Balance', title_style1_table_headbal)
            sheet.write(8, 2, self.label_filter, title_style1_table_headbal)

            row_data = 9
            for line in get_account_lines:
                if line.get('level') != 0:
                    if line.get('level') < 3:
                        sheet.write(
                            row_data, 0, str(
                                line['name']), title_style1_table_head1)
                        sheet.write(
                            row_data, 1, line['balance'],
                            title_style1_table_head_bold)
                        sheet.write(
                            row_data, 2, line['balance_cmp'],
                            title_style1_table_head_bold)
                    else:
                        sheet.write(row_data, 0, '    ' +
                                    str(line['name']),
                                    title_style1_table_normal)
                        sheet.write(
                            row_data, 1, line['balance'],
                            title_style1_table_normal_right)
                        sheet.write(
                            row_data, 2, line['balance_cmp'],
                            title_style1_table_normal_right)
                    row_data += 1

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


class AccountingFinanceReportOutputWizard(models.Model):
    _name = 'accounting.finance.report.output.wizard'
    _description = 'Wizard to store the Excel output'

    xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format',
        default='Trial_Balance.xls')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
