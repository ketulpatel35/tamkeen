# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")

    @api.model
    def create(self, vals):
        if self._context and self._context.get('segment_vals'):
            segment_vals = self._context.get('segment_vals')
            vals.update({
                'cost_centre_id': segment_vals['cost_centre_id'],
#                 'account_analytic_id': segment_vals['account_analytic_id']
            })
        return super(AccountMove, self).create(vals)

    @api.multi
    def button_cancel(self):
        super(AccountMove, self).button_cancel()
        for move in self:
            for line in move.line_ids:
                line.analytic_line_ids.sudo().unlink()
        return True

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')

    @api.model
    def create(self, vals):
        if vals and vals.get('invoice_id'):
            invoice_id = vals.get('invoice_id')
            inv = self.env['account.invoice'].search([('id', '=', invoice_id)])
            vals['cost_centre_id'] = \
                inv.cost_centre_id and inv.cost_centre_id.id
#             vals['analytic_account_id'] = \
#                 inv.account_analytic_id and inv.account_analytic_id.id
        if vals and vals.get('payment_id'):
            payment_id = vals.get('payment_id')
            payment = \
                self.env['account.payment'].search([('id', '=', payment_id)])
            vals['cost_centre_id'] = \
                payment.cost_centre_id and payment.cost_centre_id.id
#             vals['analytic_account_id'] = \
#                 payment.account_analytic_id and payment.account_analytic_id.id
        res = super(AccountMoveLine, self).create(vals)
        return res


class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    @api.multi
    def unlink(self):
        for rec in self:
            print "rec.move_id.move_id::", rec.move_id.move_id.state
            if rec.move_id and rec.move_id.move_id\
                and rec.move_id.move_id.state == 'posted':
                raise UserError(_('You cannot delete Analytic Entries for Posted Move! '))
        return super(AccountAnalyticLine, self).unlink()
