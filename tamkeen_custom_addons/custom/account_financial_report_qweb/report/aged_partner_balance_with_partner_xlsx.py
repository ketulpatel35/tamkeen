# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class AgedPartnerBalancePartnerXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(AgedPartnerBalancePartnerXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Aged Partner Balance')

    def _get_report_columns(self, report):
        return {
            0: {'header': _('Sr.'), 'field': '', 'width': 10},
            1: {'header': _('Partner'), 'field': 'partner', 'width': 50},
            2: {'header': _('Balance'),
                'width': 14},
            3: {'header': _('0-30 Days'),
                'type': 'amount',
                'width': 14},
            4: {'header': _('31-60 Days'),
                'type': 'amount',
                'width': 14},
            5: {'header': _('61-90 Days'),
                'width': 14},
            6: {'header': _('91-120 Days'),
                'width': 14},
            7: {'header': _('121-180 Days'),
                'width': 14},
            8: {'header': _('181-360 Days'),
                'width': 14},
            9: {'header': _('Above 361 Days'),
                 'width': 14},
        }

    def _get_report_filters(self, report):
        return [
            [_('Date at filter'), report.date_at],
            [_('Target moves filter'),
                _('All posted entries') if report.only_posted_moves
                else _('All entries')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _get_col_pos_footer_label(self, report):
        return 0

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report):
        # For each account
        self.write_array_header()
        if not report.filter_partner_ids and not report.filter_account_ids:
            report._cr.execute("""
                select partner,COALESCE(sum(amount_residual),0) as residual,COALESCE(sum(age_30_days),0) as age_30,
                    COALESCE(sum(current),0) as current,
                    COALESCE(sum(age_60_days),0) as age_60,COALESCE(sum(age_90_days),0) as age_90,
                    COALESCE(sum(age_120_days),0) as age_120,COALESCE(sum(age_180_days),0) as age_180,COALESCE(sum(age_360_days),0) as age_360,
                    COALESCE(sum(older),0) as age_361
                from report_aged_partner_balance_partner_qweb_line where report_partner_id in (
                    select id from report_aged_partner_balance_partner_qweb_partner where report_account_id in (
                    select id from report_aged_partner_balance_partner_qweb_account where report_id=%s)) group by partner
            """ % (report.id))
        elif report.filter_partner_ids and not report.filter_account_ids:
            report._cr.execute("""
                select partner,COALESCE(sum(amount_residual),0) as residual,COALESCE(sum(age_30_days),0) as age_30,
                    COALESCE(sum(current),0) as current,
                    COALESCE(sum(age_60_days),0) as age_60,COALESCE(sum(age_90_days),0) as age_90,
                    COALESCE(sum(age_120_days),0) as age_120,COALESCE(sum(age_180_days),0) as age_180,COALESCE(sum(age_360_days),0) as age_360,
                    COALESCE(sum(older),0) as age_361
                from report_aged_partner_balance_partner_qweb_line where report_partner_id in (
                    select id from report_aged_partner_balance_partner_qweb_partner where report_account_id in (
                    select id from report_aged_partner_balance_partner_qweb_account where report_id=%s)
                    and partner_id in (%s))
                     group by partner
            """ % (report.id, ','.join(map(str, report.filter_partner_ids.ids))))
        elif not report.filter_partner_ids and report.filter_account_ids:
            report._cr.execute("""
                select partner,COALESCE(sum(amount_residual),0) as residual,COALESCE(sum(age_30_days),0) as age_30,
                    COALESCE(sum(current),0) as current,
                    COALESCE(sum(age_60_days),0) as age_60,COALESCE(sum(age_90_days),0) as age_90,
                    COALESCE(sum(age_120_days),0) as age_120,COALESCE(sum(age_180_days),0) as age_180,COALESCE(sum(age_360_days),0) as age_360,
                    COALESCE(sum(older),0) as age_361
                from report_aged_partner_balance_partner_qweb_line where report_partner_id in (
                    select id from report_aged_partner_balance_partner_qweb_partner where report_account_id in (
                    select id from report_aged_partner_balance_partner_qweb_account where report_id=%s and account_id in (%s))
                     group by partner
            """ % (report.id, ','.join(map(str, report.filter_account_ids.ids))))
        elif report.filter_partner_ids and report.filter_account_ids:
            report._cr.execute("""
                select partner,COALESCE(sum(amount_residual),0) as residual,COALESCE(sum(age_30_days),0) as age_30,
                    COALESCE(sum(current),0) as current,
                    COALESCE(sum(age_60_days),0) as age_60,COALESCE(sum(age_90_days),0) as age_90,
                    COALESCE(sum(age_120_days),0) as age_120,COALESCE(sum(age_180_days),0) as age_180,COALESCE(sum(age_360_days),0) as age_360,
                    COALESCE(sum(older),0) as age_361
                from report_aged_partner_balance_partner_qweb_line where report_partner_id in (
                    select id from report_aged_partner_balance_partner_qweb_partner where report_account_id in (
                    select id from report_aged_partner_balance_partner_qweb_account where report_id=%s and account_id in (%s))
                    and partner_id in (%s))
                     group by partner
            """ % (report.id, ','.join(map(str, report.filter_account_ids.ids)), ','.join(map(str, report.filter_partner_ids.ids))))
        datas = report._cr.dictfetchall()
        count = 1
        for data in datas:
            col_pos = 0
            self.sheet.write_number(self.row_pos, col_pos, count)
            col_pos += 1
            value = data.get('partner')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('residual')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_30') + data.get('current')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_60')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_90')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_120')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_180')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_360')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            value = data.get('age_361')
            if isinstance(value, (str, unicode)):
                self.sheet.write(
                    self.row_pos, col_pos, value)
            else:
                self.sheet.write_number(
                    self.row_pos, col_pos, value, self.format_amount
                )
            col_pos += 1
            self.row_pos += 1
            count += 1

    def write_ending_balance(self, my_object):
        """
            Specific function to write ending partner balance
            for Aged Partner Balance
        """
        name = None
        label = _('Partner cumul aged balance')
        super(AgedPartnerBalancePartnerXslx, self).write_ending_balance(
            my_object, name, label
        )

    def write_account_footer(self, report, account, label, field_name,
                             string_format, amount_format, amount_is_percent):
        """
            Specific function to write account footer for Aged Partner Balance
        """
        col_pos_footer_label = self._get_col_pos_footer_label(report)
        for col_pos, column in self.columns.iteritems():
            if col_pos == col_pos_footer_label or column.get(field_name):
                if col_pos == col_pos_footer_label:
                    value = label
                else:
                    value = getattr(account, column[field_name])
                cell_type = column.get('type', 'string')
                if cell_type == 'string' or col_pos == col_pos_footer_label:
                    self.sheet.write_string(self.row_pos, col_pos, value or '',
                                            string_format)
                elif cell_type == 'amount':
                    number = float(value)
                    if amount_is_percent:
                        number /= 100
                    self.sheet.write_number(self.row_pos, col_pos,
                                            number,
                                            amount_format)
            else:
                self.sheet.write_string(self.row_pos, col_pos, '',
                                        string_format)

        self.row_pos += 1


AgedPartnerBalancePartnerXslx(
    'report.account_financial_report_qweb.report_aged_partner_balance_with_partner_xlsx',
    'report_aged_partner_balance_partner_qweb',
    parser=report_sxw.rml_parse
)
