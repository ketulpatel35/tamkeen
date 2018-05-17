# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models


class AccountAnalyticJournal(models.Model):
    _name = 'account.analytic.journal'
    _description = 'Analytic Journal'

    name = fields.Char('Journal Name', required=True)
    code = fields.Char('Journal Code')
    active = fields.Boolean('Active', help="If the active field is set to "
                                           "False, it will allow you to hide "
                                           "the analytic journal without "
                                           "removing it.", default=True)
    type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase'),
                             ('cash', 'Cash'), ('general', 'General'),
                             ('situation', 'Situation')], 'Type',
                            required=True,
                            help="Gives the type of the analytic journal. "
                                 "When it needs for a document (eg: an "
                                 "invoice) to create analytic entries, "
                                 "Odoo will look for a matching journal of "
                                 "the same type.", default='general')
    line_ids = fields.One2many('account.analytic.line', 'journal_id',
                               'Lines', copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self:
                                 self.env.user.company_id.id)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    analytic_journal_id = fields.Many2one('account.analytic.journal',
                                          string='Analytic Journal',
                                          help="Journal for analytic entries")


class AccountJournalLine(models.Model):
    _inherit = "account.analytic.line"

    journal_id = fields.Many2one('account.analytic.journal',
                                 string='Analytic Journal',
                                 index=True,
                                 help="Journal for analytic entries")
