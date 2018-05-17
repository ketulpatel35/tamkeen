# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class GeneralLedgerXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(GeneralLedgerXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('General Ledger')

    def _get_report_columns(self, report):
        if not report.show_details:
            return {
                0: {'header': _('Ref - Label'), 'field': 'label', 'width': 11},
                5: {'header': _('Balance'), 'field': 'label', 'width': 18},
                6: {'header': _('Debit'),
                    'field': 'debit',
                    'field_initial_balance': 'initial_debit',
                    'field_final_balance': 'final_debit',
                    'type': 'amount',
                    'width': 14},
                7: {'header': _('Credit'),
                     'field': 'credit',
                     'field_initial_balance': 'initial_credit',
                     'field_final_balance': 'final_credit',
                     'type': 'amount',
                     'width': 14},
                8: {'header': _('Cumul. Bal.'),
                     'field': 'cumul_balance',
                     'field_initial_balance': 'initial_balance',
                     'field_final_balance': 'final_balance',
                     'type': 'amount',
                     'width': 14},
            }
        else:
            return {
                0: {'header': _('Date'), 'field': 'date', 'width': 11},
                1: {'header': _('Entry'), 'field': 'entry', 'width': 18},
                2: {'header': _('Journal'), 'field': 'journal', 'width': 8},
                3: {'header': _('Account'), 'field': 'account', 'width': 9},
                4: {'header': _('Partner'), 'field': 'partner', 'width': 25},
                5: {'header': _('Ref - Label'), 'field': 'label', 'width': 40},
                6: {'header': _('Cost center Code'), 'field': 'cost_center',
                    'width': 15},
                7: {'header': _('Cost center Name'), 'field': 'cost_center_name',
                    'width': 15},
                8: {'header': _('Rec.'), 'field': 'matching_number', 'width': 5},
                9: {'header': _('Debit'),
                    'field': 'debit',
                    'field_initial_balance': 'initial_debit',
                    'field_final_balance': 'final_debit',
                    'type': 'amount',
                    'width': 14},
                10: {'header': _('Credit'),
                     'field': 'credit',
                     'field_initial_balance': 'initial_credit',
                     'field_final_balance': 'final_credit',
                     'type': 'amount',
                     'width': 14},
                11: {'header': _('Cumul. Bal.'),
                     'field': 'cumul_balance',
                     'field_initial_balance': 'initial_balance',
                     'field_final_balance': 'final_balance',
                     'type': 'amount',
                     'width': 14},
                12: {'header': _('Cur.'), 'field': 'currency_name', 'width': 7},
                13: {'header': _('Amount cur.'),
                     'field': 'amount_currency',
                     'type': 'amount',
                     'width': 14},
            }

    def _get_report_filters(self, report):
        return [
            [_('Date range filter'),
                _('From: %s To: %s') % (report.date_from, report.date_to)],
            [_('Target moves filter'),
                _('All posted entries') if report.only_posted_moves
                else _('All entries')],
            [_('Account balance at 0 filter'),
                _('Hide') if report.hide_account_balance_at_0 else _('Show')],
            [_('Centralize filter'),
                _('Yes') if report.centralize else _('No')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_col_pos_initial_balance_label(self):
        return 5

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def write_array_header_with_out_details(self):
        """Write array header on current line using all defined columns name.
        Columns are defined with `_get_report_columns` method.
        """
        for col_pos, column in self.columns.iteritems():
            if col_pos == 0:
                self.sheet.merge_range(
                    self.row_pos, col_pos, self.row_pos, col_pos + 4,
                    column['header'], self.format_header_center)
            self.sheet.write(self.row_pos, col_pos, column['header'],
                             self.format_header_center)
        self.row_pos += 1

    def _generate_report_content(self, workbook, report):
        show_details = report.show_details
        if not show_details:
            self.write_array_header_with_out_details()
        # For each account
        for account in report.account_ids:
            if show_details:
                # Write account title
                self.write_array_title(account.code + ' - ' + account.name)
                if not account.partner_ids:
                    # Display array header for move lines
                    self.write_array_header()

                    # Display initial balance line for account
                    self.write_initial_balance(account, _('Initial balance'))

                    # Display account move lines
                    for line in account.move_line_ids:
                        self.write_line(line)

                else:
                    # For each partner
                    for partner in account.partner_ids:
                        # Write partner title
                        self.write_array_title(partner.name)

                        # Display array header for move lines
                        self.write_array_header()

                        # Display initial balance line for partner
                        self.write_initial_balance(partner, _('Initial balance'))

                        # Display account move lines
                        for line in partner.move_line_ids:
                            self.write_line(line)

                        # Display ending balance line for partner
                        self.write_ending_balance(partner, 'partner')

                        # Line break
                        self.row_pos += 1
            else:
                self.write_initial_balance(account, _('Initial balance'))

            # Display ending balance line for account
            self.write_ending_balance(account, 'account')

            if show_details:
                # 2 lines break
                self.row_pos += 2

    def write_ending_balance(self, my_object, type_object):
        """Specific function to write ending balance for General Ledger"""
        if type_object == 'partner':
            name = my_object.name
            label = _('Partner ending balance')
        elif type_object == 'account':
            name = my_object.code + ' - ' + my_object.name
            label = _('Ending balance')
        super(GeneralLedgerXslx, self).write_ending_balance(
            my_object, name, label
        )


GeneralLedgerXslx(
    'report.account_financial_report_qweb.report_general_ledger_xlsx',
    'report_general_ledger_qweb',
    parser=report_sxw.rml_parse
)
