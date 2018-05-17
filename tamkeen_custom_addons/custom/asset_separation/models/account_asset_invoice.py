import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_analytic = fields.Boolean('Required Analytic Account')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'


    @api.one
    def asset_create(self):
        if self.asset_category_id:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal_signed,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.company_currency_id.id,
                'date': self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
            }
            changed_vals = self.env[
                'account.asset.asset'].onchange_category_id_values(
                vals['category_id'])
            vals.update(changed_vals['value'])
            asset = self.env['account.asset.asset'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True

    @api.one
    def asset_create(self):
        company_currency = self.invoice_id.company_currency_id
        current_currency = self.invoice_id.currency_id
        amount = self.price_unit
        if company_currency != current_currency:
            amount = current_currency.compute(self.price_unit,
                                              company_currency)
        if self.asset_category_id and amount >= \
            self.asset_category_id \
            .asset_consideration_value:
            if self.asset_category_id and self.quantity > 1:
                counter = self.quantity
                # raise osv.except_osv(_('Error!'),line.quantity)
                while counter != 0:
                    vals = {
                        'name': self.name,
                        'code': self.invoice_id.number or False,
                        'category_id': self.asset_category_id.id,
                        'value': amount,
                        'partner_id': self.invoice_id.partner_id.id,
                        'company_id': self.invoice_id.company_id.id,
                        'currency_id': self.invoice_id.company_currency_id.id,
                        'date': self.invoice_id.date_invoice,
                        'invoice_id': self.invoice_id.id,
                    }
                    changed_vals = self.env['account.asset.asset'] \
                        .onchange_category_id_values(vals['category_id'])
                    vals.update(changed_vals['value'])
                    asset = self.env['account.asset.asset'].create(vals)
                    if self.asset_category_id.open_asset:
                        asset.validate()
                    counter = counter - 1

                return True
            return super(AccountInvoiceLine, self).asset_create()


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.constrains('analytic_id', 'company_id')
    def check_account_analytic_required(self):
        """
        check analytic account required or not in company
        :return:
        """
        if self.company_id.allow_analytic:
            if not self.analytic_id:
                raise ValidationError(
                    _("Analytic account must be required."))

    @api.model
    def create(self, vals):
        """
        for date validation
        :param vals:
        :return:
        """
        res = super(AccountAssetAsset, self).create(vals)
        for rec in res:
            if rec.category_id.is_month_last_date:
                for line in rec.depreciation_line_ids[1:-1]:
                    line_date = datetime.strptime(line.depreciation_date,
                                                  DF).date()
                    current_month_last_day = calendar.monthrange(
                        line_date.year, line_date.month)
                    extra_days = current_month_last_day[1] - line_date.day
                    last_date = line_date + timedelta(extra_days)
                    line.depreciation_date = str(last_date)

        return res

    @api.model
    def compute_generated_entries(self, date, asset_type=None):
        # Entries generated : one by grouped category and one by asset
        # from ungrouped category
        created_move_ids = []
        type_domain = []
        category_ids = self.env.context.get('category_ids')
        if asset_type:
            type_domain = [('type', '=', asset_type)]

        ungrouped_assets = self.env['account.asset.asset'].search(
            type_domain + [('state', '=', 'open'),
                           ('category_id.group_entries', '=', False),
                           ('category_id', 'in', category_ids)])
        created_move_ids += \
            ungrouped_assets._compute_entries(date, group_entries=False)
        dom = type_domain + [('group_entries', '=', True)]
        for grouped_category in self.env['account.asset.category'].search(dom):
            assets = self.env['account.asset.asset'].search([
                ('state', '=', 'open'),
                ('category_id', '=', grouped_category.id),
                ('category_id', 'in', category_ids)])
            created_move_ids += assets._compute_entries(date,
                                                        group_entries=True)
        return created_move_ids


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    is_month_last_date = fields.Boolean('Month last date')
    asset_consideration_value = fields.Float('Asset Consideration Value')


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _inherit = 'asset.depreciation.confirmation.wizard'

    category_ids = fields.Many2many('account.asset.category',
                                    'asset_depreciation_wiz_rel', 'asset_id',
                                    'catg_id', string='Asset Category')

    @api.multi
    def asset_compute(self):
        self.ensure_one()
        context = dict(self._context)
        context.update({'category_ids': self.category_ids.ids})
        created_move_ids = self.env['account.asset.asset'].with_context(
            context).compute_generated_entries(
            self.date, asset_type=context.get('asset_type'))
        return {
            'name': _('Created Asset Moves') if context.get(
                'asset_type') == 'purchase' else _('Created Revenue Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': "[('id','in',[" + ','.join(
                map(str, created_move_ids)) + "])]",
            'type': 'ir.actions.act_window',
        }

