# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    certificate_of_completion_id = fields.Many2one(
        'certificate.of.completion', string='Certificate of Completion')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    certificate_of_completion_id = fields.Many2one(
        'certificate.of.completion',  store=True,
        related='invoice_id.certificate_of_completion_id', readonly='1')
