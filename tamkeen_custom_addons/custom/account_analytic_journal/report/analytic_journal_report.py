# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo.report import report_sxw
from odoo import models
from odoo.api import Environment


# Use period and Journal for selection or resources
#
class AccountAnalyticJournal(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AccountAnalyticJournal, self).__init__(cr, uid, name,
                                                     context=context)
        date_from = False
        date_to = False
        if context and context.get('form'):
            date_from = context['form']['date_from']
            date_to = context['form']['date_to']
        self.localcontext.update({
            'date_from': date_from,
            'date_to': date_to,
            # 'time': time,
            'lines': self._lines,
            'lines_a': self._lines_a,
            'sum_general': self._sum_general,
            'sum_analytic': self._sum_analytic,
        })

    def _lines(self, journal_rec, date1, date2):
        env = Environment(journal_rec._cr, journal_rec._uid,
                          journal_rec._context)
        self.cr.execute('SELECT DISTINCT move_id FROM account_analytic_line '
                        'WHERE (date>=%s) AND (date<=%s) AND (journal_id=%s) '
                        'AND (move_id is not null)', (date1, date2,
                                                      journal_rec.id,))
        ids = map(lambda x: x[0], self.cr.fetchall())
        return env['account.move.line'].browse(ids)

    def _lines_a(self, move_id, journal_rec, date1, date2):
        env = Environment(journal_rec._cr, journal_rec._uid,
                          journal_rec._context)
        analytic_line_obj = env['account.analytic.line']
        analytic_line_rec = analytic_line_obj.search([
            ('move_id', '=', move_id), ('journal_id', '=', journal_rec.id),
            ('date', '>=', date1), ('date', '<=', date2)])
        if not analytic_line_rec:
            return analytic_line_obj
        return analytic_line_rec

    def _sum_general(self, journal_rec, date1, date2):
        self.cr.execute('SELECT SUM(debit-credit) FROM account_move_line '
                        'WHERE id IN (SELECT move_id FROM '
                        'account_analytic_line WHERE (date>=%s) AND ('
                        'date<=%s) AND (journal_id=%s) AND (move_id is not '
                        'null))', (date1, date2, journal_rec.id))
        sum_general = self.cr.fetchall()[0][0] or 0
        return sum_general

    #
    def _sum_analytic(self, journal_rec, date1, date2):
        self.cr.execute(
            "SELECT SUM(amount) FROM account_analytic_line WHERE date>=%s "
            "AND date<=%s AND journal_id=%s", (date1, date2, journal_rec.id))
        res = self.cr.dictfetchone()['sum'] or 0
        return res


class ReportAnalyticJournal(models.AbstractModel):
    _name = 'report.account_analytic_journal.report_journal_analytic'
    _inherit = 'report.abstract_report'
    _template = 'account_analytic_journal.report_journal_analytic'
    _wrapped_report_class = AccountAnalyticJournal

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
