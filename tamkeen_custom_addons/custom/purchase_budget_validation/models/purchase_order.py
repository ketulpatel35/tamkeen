from odoo import models, api, fields
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.one
    @api.depends('account_analytic_id')
    def _get_allowed_budget(self):
        self.allowed_budget = 0.0
        self.commited_budget = 0.0
        self.remaining_budget = 0.0
        amount = 0.0
        amount2 = 0.0
        commited = 0.0
        if self.account_analytic_id:
            create_date = False
            if self.create_date:
                create_date = datetime.strptime(self.create_date, '%Y-%m-%d '
                                                '%H:%M:%S').date()
            else:
                create_date = datetime.now().date()
            for line in self.account_analytic_id.crossovered_budget_line:
                line_date_from = datetime.strptime(line.date_from,
                                                   '%Y-%m-%d').date()
                line_date_to = datetime.strptime(line.date_to,
                                                 '%Y-%m-%d').date()
                if line.crossovered_budget_id.state in \
                    ['validate', 'done'] and line.planned_amount < 0 \
                        and line_date_to >= create_date >= line_date_from:
                    amount += line.planned_amount
                    amount2 += line.practical_amount
            for pr_rec in self.env['purchase.requisition'].search(
                    [('account_analytic_id', '=', 
                      self.account_analytic_id.id),
                                       ('state', 'in', ['budget',
                                                        'ceo'
                                                        'purchase_app',
                                                        'in_progress',
                                                        'open'])]):
                create_date = datetime.strptime(pr_rec.create_date, 
                                                '%Y-%m-%d %H:%M:%S').date()
                estimated = 0.0
                estimated = pr_rec.estimated_cost
                po_obj = self.env['purchase.order'].search([('requisition_id',
                                                             '=', pr_rec.id),
                                                            ('state', 'not in',
                                                             ['draft', 'sent',
                                                              'bid'])])
                if po_obj:
                    estimated = 0.0
                for po in po_obj:
                    estimated += po.amount_total
                commited += estimated
            self.commited_budget = commited
            self.allowed_budget = amount * -1
            self.remaining_budget = self.allowed_budget - \
                (self.commited_budget + amount2)

    allowed_budget = fields.Float('Allowed Budget',
                                  compute='_get_allowed_budget')
    commited_budget = fields.Float('Commited Budget',
                                   compute='_get_allowed_budget')
    remaining_budget = fields.Float('Remaining Budget',
                                    compute='_get_allowed_budget')

    @api.multi
    def budget_po_action(self):
        lst_lin = []
        result = {}
        lin = self.env['crossovered.budget.lines'].search([(
            'analytic_account_id', '=', self.account_analytic_id.id)])
        if lin:
            for line in lin:
                lst_lin.append(line.id)
        if lst_lin:
            result = {
                "type": "ir.actions.act_window",
                "res_model": "crossovered.budget.lines",
                "views": [[False, "tree"], [False, "form"]],
                "domain": [["id", "in", lst_lin]],
                "context": {"create": False},
                "name": "Budgets",
            }
        return result
