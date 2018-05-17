# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    cost_centre_id = fields.Many2one('bs.costcentre', string='Cost Center')
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')

    @api.onchange('cost_centre_id', 'account_analytic_id')
    def _po_onchange_cost_center(self):
        """
        update cost center in po line if its blank.
        :return:
        """
        if self._context and self._context.get('p_cost'):
            if self.cost_centre_id:
                for po_line in self.order_line:
                    po_line.cost_centre_id = self.cost_centre_id.id
            if self.account_analytic_id:
                for po_line in self.order_line:
                    po_line.account_analytic_id = self.account_analytic_id.id

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        super(PurchaseOrder, self)._onchange_requisition_id()
        order_lines_lst = []
        if self.requisition_id:
            requisition = self.requisition_id
            count = 0
            for req_line in requisition.line_ids:
                order_line = self.order_line[count]
                cost_centre_id = \
                    req_line.cost_centre_id and req_line.cost_centre_id.id or \
                    False
                line_data = {
                    'name': order_line.name,
                    'product_id': order_line.product_id.id,
                    'product_uom': order_line.product_uom.id,
                    'product_qty': order_line.product_qty,
                    'price_unit': order_line.price_unit,
                    'date_planned': order_line.date_planned,
                    'procurement_ids': [
                        (6, 0, [order_line.procurement_ids.id])] if
                    order_line.procurement_ids else False,
                    'account_analytic_id': order_line.account_analytic_id.id,
                    'cost_centre_id': cost_centre_id,
                    'product_id': req_line.product_id.id
                }
                count += 1
                order_lines_lst.append(line_data)
        self.order_line = order_lines_lst

    # @api.one
    # @api.constrains('order_line')
    # def same_cost_center_valdation(self):
    #     for rec in self:
    #         if rec.cost_centre_id:
    #             for line_rec in self.order_line:
    #                 if rec.cost_centre_id != line_rec.cost_centre_id:
    #                     raise Warning(_(
    #                         'cost centre should be same in order line.'))

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        purchase_req_obj = self.env['purchase.requisition']
        ctx = dict(self._context)
        if 'active_id' in ctx and ctx.get('active_id'):
            po_red_id = purchase_req_obj.search(
                [('id', '=', ctx.get('active_id'))])
            if po_red_id:
                if po_red_id.cost_centre_id:
                    res.update({'cost_centre_id': po_red_id.cost_centre_id.id})
                if po_red_id.account_analytic_id:
                    res.update({'account_analytic_id':
                                    po_red_id.account_analytic_id.id})
        return res

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            for pick in rec.picking_ids:
                pick.cost_centre_id = rec.cost_centre_id.id
                for pick_line in pick.move_lines:
                    pick_line.cost_centre_id = rec.cost_centre_id.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cost_centre_id = fields.Many2one('bs.costcentre',
                                     string='Cost Center')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderLine, self).default_get(fields)
        ctx = dict(self._context)
        if ctx.get('analytic_account_id'):
            res.update({'analytic_account_id': ctx.get('analytic_account_id')})
        if ctx.get('cost_centre_id'):
            res.update({'cost_centre_id': ctx.get('cost_centre_id')})
        return res
