# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
import time
from odoo import api, fields, models


class AccountAnalyticJournalReport(models.TransientModel):
    _name = 'account.analytic.journal.report'
    _description = 'Account Analytic Journal'

    date1 = fields.Date('Start of period', required=True,
                        default=lambda *a: time.strftime('%Y-01-01'))
    date2 = fields.Date('End of period', required=True,
                        default=lambda *a: time.strftime('%Y-%m-%d'))
    analytic_account_journal_id = fields.Many2many(
        'account.analytic.journal', 'account_analytic_journal_name',
        'journal_line_id', 'journal_print_id', 'Analytic Journals',
        required=True)

    def check_report(self):
        ids_list = self.analytic_account_journal_id.ids
        datas = {'ids': ids_list,
                 'model': 'account.analytic.journal'}
        ctx = self._context.copy()
        ctx['active_model'] = 'account.analytic.journal'
        ctx['active_ids'] = ids_list
        ctx['form'] = {'date_from': self.date1,
                       'date_to': self.date2}
        return {
            'type': 'ir.actions.report.xml',
            'report_name':
                'account_analytic_journal.report_journal_analytic',
            'data': datas,
            'context': ctx
        }

    @api.model
    def default_get(self, fields):
        res = super(AccountAnalyticJournalReport, self).default_get(fields)
        journal_ids = self._context.get('active_ids', False)
        if not journal_ids:
            journal_ids = self.env['account.analytic.journal'].search([]).ids
        res.update({'analytic_account_journal_id': journal_ids})
        return res
