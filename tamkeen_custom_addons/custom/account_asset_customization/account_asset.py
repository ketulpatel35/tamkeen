from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class account_asset_asset(models.Model):
    _inherit = "account.asset.asset"

    @api.depends('depreciation_line_ids.amount')
    def _compute_total_depreciation_value(self):
        for rec in self:
            for line in rec.depreciation_line_ids:
                rec.total_depreciation_value += line.amount

    state = fields.Selection([('draft', 'Draft'),
                              ('open', 'Running'),
                              ('to_close', 'To Be Closed'),
                              ('close', 'Close')],
                             string='Status',
                             required=True,
                             copy=False,
                             track_visibility='onchange',
                             help="When an asset is created,"
                                  " the status is 'Draft'.\n If"
                                  " the asset i`s confirmed,"
                                  " the status goes in 'Running'"
                                  " and the depreciation lines"
                                  " can be posted in the accounting."
                                  "\n You can manually close an asset"
                                  " when the depreciation is over."
                                  " If the last line of depreciation"
                                  " is posted, the asset"
                                  " automatically goes in"
                                  " that status.")
    total_depreciation_value = fields.Float(
        compute='_compute_total_depreciation_value',
        string='Total Depreciation Value')

    @api.multi
    def send_to_close(self):
        for rec in self:
            return rec.write({'state': 'to_close'})


    @api.multi
    def check_validation_depreciation(self):
        """
        check validation for depreciation
        :return:
        """
        for rec in self:
            total_depreciation = 0.0
            value = rec.value - rec.salvage_value
            for line in rec.depreciation_line_ids:
                total_depreciation += line.amount
            if total_depreciation and value:
                if total_depreciation != value:
                    min_depreciation = total_depreciation - 1
                    max_depreciation = total_depreciation + 1
                    if value < min_depreciation or value > max_depreciation:
                        raise ValidationError(_("The total of the depreciation "
                                                "lines should equal the difference"
                                                " between the gross value and the "
                                                "salvage value"))

    @api.constrains('depreciation_line_ids')
    def _check_discount(self):
        for rec in self:
            rec.check_validation_depreciation()


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    @api.multi
    def create_grouped_move(self, post_move=True):
        if not self.exists():
            return []

        created_moves = self.env['account.move']
        category_id = self[0].asset_id.category_id  # we can suppose that all lines have the same category
        depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)
        amount = 0.0
        for line in self:
            # Sum amount of all depreciation lines
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount += current_currency.compute(line.amount, company_currency)

        name = category_id.name + _(' (grouped) - ') + depreciation_date
        move_line_1 = {
            'name': name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': category_id.journal_id.id,
            'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
        }
        move_line_2 = {
            'name': name,
            'account_id': category_id.account_depreciation_expense_id.id,
            'credit': 0.0,
            'debit': amount,
            'journal_id': category_id.journal_id.id,
            'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
        }
        move_vals = {
            'ref': category_id.name,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        move = self.env['account.move'].create(move_vals)
        self.write({'move_id': move.id, 'move_check': True})
        created_moves |= move

        if post_move and created_moves:
            self.post_lines_and_close_asset()
            created_moves.post()
        return [x.id for x in created_moves]
