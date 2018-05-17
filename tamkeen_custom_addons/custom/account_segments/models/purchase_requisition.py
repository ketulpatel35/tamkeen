# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          track_visibility='onchange',
                                          string="Analytic Account")

    @api.onchange('cost_centre_id', 'account_analytic_id')
    def _onchange_cost_center(self):
        """
        update line based on cost center
        :return:
        """
        if self.cost_centre_id:
            for line in self.line_ids:
                line.cost_centre_id = self.cost_centre_id.id
        if self.account_analytic_id:
            for line in self.line_ids:
                line.account_analytic_id = self.account_analytic_id.id
    # @api.one
    # @api.constrains('line_ids')
    # def same_cost_center(self):
    #     for rec in self:
    #         if rec.cost_centre_id:
    #             for line_rec in self.line_ids:
    #                  if rec.cost_centre_id != line_rec.cost_centre_id:
    #                      raise Warning(_('Cost Centre should be same in '
    #                                      'line.'))


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequisitionLine, self).default_get(fields)
        ctx = dict(self._context)
        if ctx.get('cost_centre_id'):
            res.update({'cost_centre_id': ctx.get('cost_centre_id')})
        if ctx.get('account_analytic_id'):
            res.update({'account_analytic_id': ctx.get('account_analytic_id')})
        return res
