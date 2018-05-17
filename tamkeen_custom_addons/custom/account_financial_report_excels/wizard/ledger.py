# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
# import time
from odoo import models, fields, api


class PartnerLedgerCustomized(models.TransientModel):
    _inherit = 'account.report.partner.ledger'
    _description = "Partner Ledger Report"

    partner_ids = fields.Many2many(
        'res.partner',
        'partner_general_ledger_rel',
        'report_id',
        'partner_id',
        string='Partners')

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids',
                                  'partner_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = \
            dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data)

    @api.onchange('result_selection')
    def onchange_result_selection(self):
        domain = []
        res_partner = self.env['res.partner']
        self.partner_ids = False
        if not self.result_selection:
            domain = []
        elif self.result_selection == 'customer':
            partner_ids = res_partner.search([('customer', '=', True)]).ids
            domain = [('id', 'in', partner_ids)]
        elif self.result_selection == 'supplier':
            partner_ids = res_partner.search([('supplier', '=', True)]).ids
            domain = [('id', 'in', partner_ids)]
        if self.partner_ids:
            self.partner_ids = res_partner
        return {'domain': {'partner_ids': domain}}

# class ReportPartnerLedgerInherit(models.AbstractModel):
#     _inherit = 'report.account.report_partnerledger'
#
#     @api.model
#     def render_html(self, docids, data=None):
#         data['computed'] = {}
#
#         obj_partner = self.env['res.partner']
#         query_get_data = self.env['account.move.line']\
#             .with_context(data['form']
#                           .get('used_context', {}))._query_get()
#         data['computed']['move_state'] = ['draft', 'posted']
#         if data['form'].get('target_move', 'all') == 'posted':
#             data['computed']['move_state'] = ['posted']
#         result_selection = data['form'].get('result_selection', 'customer')
#         if result_selection == 'supplier':
#             data['computed']['ACCOUNT_TYPE'] = ['payable']
#         elif result_selection == 'customer':
#             data['computed']['ACCOUNT_TYPE'] = ['receivable']
#         else:
#             data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']
#
#         self.env.cr.execute("""
#                 SELECT a.id
#                 FROM account_account a
#                 WHERE a.internal_type IN %s
#                 AND NOT a.deprecated""",
#                             (tuple(data['computed']['ACCOUNT_TYPE']),))
#         data['computed']['account_ids'] = [
#             a for (a,) in self.env.cr.fetchall()]
#         params = [tuple(data['computed']['move_state']),
#                   tuple(data['computed']['account_ids'])] + query_get_data[2]
#         reconcile_clause = "" if data['form']['reconciled'] \
#             else ' AND "account_move_line".reconciled = false '
#         query = """
#                 SELECT DISTINCT "account_move_line".partner_id
#                 FROM """ + query_get_data[0] + """,
#                 account_account AS account, account_move AS am
#                 WHERE "account_move_line".partner_id IS NOT NULL
#                     AND "account_move_line".account_id = account.id
#                     AND am.id = "account_move_line".move_id
#                     AND am.state IN %s
#                     AND "account_move_line".account_id IN %s
#                     AND NOT account.deprecated
#                     AND """ + query_get_data[1] + reconcile_clause
#         self.env.cr.execute(query, tuple(params))
#         # NOTE: select only those partner's who are selected other wise all
#         partner_ids = []
#         if data['form'].get('partner_ids', False):
#             partner_ids = data['form'].get('partner_ids')
#         else:
#             partner_ids = [res['partner_id']
#                            for res in self.env.cr.dictfetchall()]
#         partners = obj_partner.browse(partner_ids)
#         partners = sorted(partners, key=lambda x: (x.ref, x.name))
#
#         docargs = {
#             'doc_ids': partner_ids,
#             'doc_model': self.env['res.partner'],
#             'data': data,
#             'docs': partners,
#             'time': time,
#             'lines': self._lines,
#             'sum_partner': self._sum_partner,
#         }
#         return self.env['report'].render(
#             'account.report_partnerledger', docargs)
#
#
# class GeneralLedgerCustomized(models.TransientModel):
#     _inherit = "account.report.general.ledger"
#     _description = "General Ledger Report"
#
#     account_ids = fields.Many2many('account.account',
#                                    'account_id', string='Accounts')
#
#     @api.multi
#     def check_report(self):
#         self.ensure_one()
#         data = {}
#         data['ids'] = self.env.context.get('active_ids', [])
#         data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
#         data['form'] = self.read(['date_from',
#                                   'date_to',
#                                   'journal_ids',
#                                   'account_ids',
#                                   'target_move'])[0]
#         used_context = self._build_contexts(data)
#         data['form']['used_context'] = \
#             dict(used_context, lang=self.env.context.get('lang', 'en_US'))
#         return self._print_report(data)
#
#
# class ReportGeneralLedgerInherit(models.AbstractModel):
#     _inherit = 'report.account.report_generalledger'
#
#     @api.model
#     def render_html(self, docids, data=None):
#         self.model = self.env.context.get('active_model')
#         docs = self.env[self.model].browse(
#             self.env.context.get('active_ids', []))
#
#         init_balance = data['form'].get('initial_balance', True)
#         sortby = data['form'].get('sortby', 'sort_date')
#         display_account = data['form']['display_account']
#         codes = []
#         if data['form'].get('journal_ids', False):
#             codes = [journal.code for journal in
#                      self.env['account.journal'].search([
#                          ('id', 'in', data['form']['journal_ids'])])]
#
#         # Note : If Accounts Are selected then the condition will
#         # execute otherwise else part will execute
#         if data['form'].get('account_ids'):
#             # for rec in data['form'].get('account_ids'):
#             accounts = self.env['account.account'].browse(
#                 data['form'].get('account_ids'))
#         else:
#             accounts = docs \
#                 if self.model == 'account.account' \
#                 else self.env['account.account'].search([])
#         accounts_res = \
#             self.with_context(data['form']
#                               .get('used_context', {}))\
#                 ._get_account_move_entry(accounts,
#                                          init_balance,
#                                          sortby,
#                                          display_account)
#         docargs = {
#             'doc_ids': docids,
#             'doc_model': self.model,
#             'data': data['form'],
#             'docs': docs,
#             'time': time,
#             'Accounts': accounts_res,
#             'print_journal': codes,
#         }
#         return self.env['report'].render(
#             'account.report_generalledger', docargs)
