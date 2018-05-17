# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import odoo.addons.decimal_precision as dp
import time
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class AccountAnalyticInvoiceLine(models.Model):
    _name = "account.analytic.invoice.line"

    def _amount_line(self):
        for line in self:
            line.price_subtotal = (line.quantity * line.price_unit)

    product_id = fields.Many2one('product.product', 'Product', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          ondelete='cascade')
    name = fields.Text('Description', required=True)
    quantity = fields.Float('Quantity', required=True, default=1)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True)
    price_subtotal = fields.Float(compute='_amount_line', string='Sub Total',
                                  digits=dp.get_precision('Account'))

    @api.onchange('product_id')
    def product_id_change(self):
        name = ''
        if not self.product_id:
            return {'value': {'price_unit': 0.0},
                    'domain': {'product_uom': []}}
        if self.product_id.list_price is not False:
            price = self.product_id.list_price
        if self.product_id.name:
            if self.product_id.description_sale:
                name += '\n' + self.product_id.description_sale
        self.name = name
        self.uom_id = self.product_id.uom_id or False
        self.price_unit = price or False

    @api.onchange('uom_id', 'price_unit')
    def uom_id_change(self):
        if self.uom_id:
            amount = self.product_id.uom_id._compute_price(self.price_unit,
                                                           self.uom_id)
            self.price_unit = amount


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    def _ca_invoiced_calc(self):
        for rec in self:
            # Search all invoice lines not in cancelled state that refer to
            # this analytic account
            inv_line_obj = self.env["account.invoice.line"]
            inv_lines = inv_line_obj.search(
                ['&', ('account_analytic_id', '=', rec.id),
                 ('invoice_id.state', 'not in', ['draft', 'cancel']),
                 ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])])
            for line in inv_lines:
                if line.invoice_id.type == 'out_refund':
                    rec.ca_invoiced -= line.price_subtotal
                else:
                    rec.ca_invoiced += line.price_subtotal

    @api.multi
    def open_sale_order_lines(self):
        if self._context is None:
            return True
        sale_ids = self.env['sale.order'].search([
            ('project_id', '=', self._context.get(
                'search_default_project_id', False)),
            ('partner_id', 'in', self._context.get(
                'search_default_partner_id', False))])
        names = [record.name for record in self]
        name = _('Sales Order Lines to Invoice of %s') % ','.join(names)
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self._context,
            'domain': [('order_id', 'in', sale_ids.ids)],
            'res_model': 'sale.order.line',
            'nodestroy': True,
        }

    @api.multi
    def _remaining_ca_calc(self):
        for account in self:
            account.remaining_ca = max(
                account.amount_max - account.ca_invoiced,
                account.fix_price_to_invoice)

    @api.multi
    def _fix_price_to_invoice_calc(self):
        sale_obj = self.env['sale.order']
        for account in self:
            sale_rec = sale_obj.search([('project_id', '=', account.id)])
            for sale in sale_rec:
                account.fix_price_to_invoice += sale.amount_untaxed
                for invoice in sale.invoice_ids:
                    if invoice.state != 'cancel':
                        account.fix_price_to_invoice -= invoice.amount_untaxed

    @api.multi
    def _get_total_estimation(self, account):
        tot_est = 0.0
        if account.fix_price_invoices:
            tot_est += account.amount_max
        return tot_est

    @api.multi
    def _get_total_invoiced(self, account):
        tot_invoiced = 0.0
        if account.fix_price_invoices:
            tot_invoiced += account.ca_invoiced
        return tot_invoiced

    @api.multi
    def _get_total_remaining(self, account):
        total_remaining = 0.0
        if account.fix_price_invoices:
            total_remaining += account.remaining_ca
        return total_remaining

    @api.multi
    def _get_total_toinvoice(self, account):
        total_toinvoice = 0.0
        if account.fix_price_invoices:
            total_toinvoice += account.fix_price_to_invoice
        return total_toinvoice

    @api.multi
    def _sum_of_fields(self):
        for account in self:
            account.est_total = self._get_total_estimation(account)
            account.invoiced_total = self._get_total_invoiced(
                account)
            account.remaining_total = self._get_total_remaining(
                account)
            account.toinvoice_total = self._get_total_toinvoice(
                account)

    @api.one
    @api.depends('company_id')
    def _compute_currency(self):
        self.currency_id = \
            self.company_id.currency_id or self.env.user.company_id.currency_id

    type = fields.Selection([
        ('view', 'Analytic View'), ('normal', 'Analytic Account'),
        ('contract', 'Contract or Project'),
        ('template', 'Template of Contract')], string='Type of Account',
        required=True, default='normal',
        help="If you select the View Type, it means you won\'t allow to create"
             " journal entries using that account.\n The type 'Analytic "
             "account' stands for usual accounts that you only want to use "
             "in accounting.\n If you select Contract or Project, it offers "
             "you the possibility to manage the validity and the invoicing "
             "options for this account.\n The special type 'Template of "
             "Contract' allows you to define a template with default data "
             "that you can reuse easily.")
    template_id = fields.Many2one('account.analytic.account',
                                  'Template of Contract')
    date_start = fields.Date('Start Date')
    date = fields.Date('Expiration Date', index=True,
                       track_visibility='onchange')
    quantity_max = fields.Float('Prepaid Service Units',
                                help='Sets the higher limit of time to work '
                                     'on the contract, based on the '
                                     'timesheet. (for instance, number of '
                                     'hours in a limited support contract.)')
    description = fields.Text('Description')

    ca_invoiced = fields.Float(compute='_ca_invoiced_calc',
                               string='Invoiced Amount',
                               digits_compute=dp.get_precision('Account'),
                               help="Total customer invoiced amount for this "
                                    "account.")
    amount_max = fields.Float('Max. Invoice Price',
                              help="Keep empty if this contract is not "
                                   "limited to a total fixed price.")
    remaining_ca = fields.Float(compute='_remaining_ca_calc',
                                string='Remaining Revenue',
                                help="Computed using the formula: Max "
                                     "Invoice Price - Invoiced Amount.",
                                digits=dp.get_precision(
                                    'Account'))
    fix_price_to_invoice = fields.Float(compute='_fix_price_to_invoice_calc',
                                        string='Remaining Time',
                                        help="Sum of quotations for this "
                                             "contract.")
    fix_price_invoices = fields.Boolean('Fixed Price')
    est_total = fields.Float(compute='_sum_of_fields',
                             multi="sum_of_all",
                             string="Total Estimation")
    invoiced_total = fields.Float(compute='_sum_of_fields',
                                  multi="sum_of_all",
                                  string="Total Invoiced")
    remaining_total = fields.Float(compute='_sum_of_fields',
                                   multi="sum_of_all",
                                   string="Total Remaining",
                                   help="Expectation of remaining income for "
                                        "this contract. Computed as the sum "
                                        "of remaining subtotals which, in "
                                        "turn, are computed as the maximum "
                                        "between '(Estimation - Invoiced)' "
                                        "and 'To Invoice' amounts")
    toinvoice_total = fields.Float(compute='_sum_of_fields',
                                   multi="sum_of_all",
                                   string="Total to Invoice",
                                   help=" Sum of everything that could be "
                                        "invoiced for this contract.")
    recurring_invoice_line_ids = fields.One2many(
        'account.analytic.invoice.line', 'analytic_account_id',
        'Invoice Lines', copy=True)
    recurring_invoices = fields.Boolean(
        'Generate recurring invoices automatically')
    recurring_rule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)'),
    ], 'Recurrency',
        help="Invoice automatically repeat at specified interval",
        default='monthly')
    recurring_interval = fields.Integer('Repeat Every',
                                        help="Repeat every ("
                                             "Days/Week/Month/Year)",
                                        default=1)
    recurring_next_date = fields.Date('Date of Next Invoice',
                                      default=lambda *a: time.strftime(
                                          '%Y-%m-%d'))
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self:
                                 self.env.user.company_id.id)
    partner_id = fields.Many2one('res.partner', 'Customer')
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist',
                                   help="The product to invoice is defined "
                                        "on the employee form, the price "
                                        "will be deducted by this pricelist "
                                        "on the product.")
    state = fields.Selection([('template', 'Template'),
                              ('draft', 'New'),
                              ('open', 'In Progress'),
                              ('pending', 'To Renew'),
                              ('close', 'Closed'),
                              ('cancelled', 'Cancelled')],
                             'Status', required=True,
                             track_visibility='onchange', copy=False,
                             default='open')

    currency_id = fields.Many2one('res.currency', compute='_compute_currency',
                                  store=True, string="Currency")

    @api.onchange('recurring_invoices', 'date_start')
    def onchange_recurring_invoices(self):
        # value = {}
        if self.date_start and self.recurring_invoices:
            self.recurring_next_date = self.date_start

    @api.onchange('template_id')
    def on_change_template(self):
        if self.template_id:
            if self.template_id.date_start and self.template_id.date:
                from_dt = datetime.strptime(self.template_id.date_start, DF)
                to_dt = datetime.strptime(self.template_id.date, DF)
                timedelta = to_dt - from_dt
                self.date = datetime.strftime(datetime.now() + timedelta, DF)
            if not self.date_start:
                self.date_start = fields.date.today()
            self.quantity_max = self.template_id.quantity_max
            self.parent_id = self.template_id.parent_id.id or False
            self.description = self.template_id.description

    @api.multi
    def recurring_create_invoice(self):
        return self._recurring_create_invoice()

    @api.model
    def _cron_recurring_create_invoice(self):
        return self._recurring_create_invoice(automatic=True)

    @api.multi
    def _recurring_create_invoice(self, automatic=False):
        invoice_ids = []
        current_date = time.strftime('%Y-%m-%d')
        if self.ids:
            contract_ids = self.ids
        else:
            contract_ids = self.search([
                ('recurring_next_date', '<=', current_date),
                ('state', '=', 'open'), ('recurring_invoices', '=', True),
                ('type', '=', 'contract')])
            if contract_ids:
                contract_ids = contract_ids.ids
        if contract_ids:
            self._cr.execute('SELECT company_id, array_agg(id) as ids FROM '
                             'account_analytic_account WHERE id IN %s GROUP '
                             'BY company_id', (tuple(contract_ids),))
            for company_id, ids in self._cr.fetchall():
                for contract in self.with_context(
                        company_id=company_id,
                        force_company=company_id).browse(ids):
                    try:
                        invoice_values = self._prepare_invoice(contract)
                        invoice_ids.append(
                            self.env['account.invoice'].create(invoice_values))
                        next_date = datetime.strptime(
                            contract.recurring_next_date or current_date,
                            "%Y-%m-%d")
                        interval = contract.recurring_interval
                        if contract.recurring_rule_type == 'daily':
                            new_date = next_date + relativedelta(
                                days=+interval)
                        elif contract.recurring_rule_type == 'weekly':
                            new_date = next_date + relativedelta(
                                weeks=+interval)
                        elif contract.recurring_rule_type == 'monthly':
                            new_date = next_date + relativedelta(
                                months=+interval)
                        else:
                            new_date = next_date + relativedelta(
                                years=+interval)
                        contract.write({
                            'recurring_next_date': new_date.strftime(
                                '%Y-%m-%d')})
                        if automatic:
                            self._cr.commit()
                    except Exception:
                        if automatic:
                            self._cr.rollback()
                            _logger.exception(
                                'Fail to create recurring invoice for '
                                'contract %s', contract.code)
                        else:
                            raise
        return invoice_ids

    @api.multi
    def _prepare_invoice(self, contract):
        invoice = self._prepare_invoice_data(contract)
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(
            contract, invoice['fiscal_position_id'])
        return invoice

    @api.multi
    def _prepare_invoice_data(self, contract):

        journal_obj = self.env['account.journal']
        fpos_obj = self.env['account.fiscal.position']
        partner = contract.partner_id

        if not partner:
            raise Warning(_("You must first select a Customer for Contract "
                            "%s!") % contract.name)

        fpos_id = fpos_obj.get_fiscal_position(partner.id)
        journal_ids = journal_obj.search([('type', '=', 'sale'), (
            'company_id', '=', contract.company_id.id or False)], limit=1)
        if not journal_ids:
            raise Warning(
                _('Please define a sale journal for the company "%s".') % (
                    contract.company_id.name or '',))

        partner_payment_term = partner.property_payment_term_id and partner. \
            property_payment_term_id.id or False

        currency_id = False
        if contract.pricelist_id:
            currency_id = contract.pricelist_id.currency_id.id
        elif partner.property_product_pricelist:
            currency_id = partner.property_product_pricelist.currency_id.id
        elif contract.company_id:
            currency_id = contract.company_id.currency_id.id

        invoice = {
            'account_id': partner.property_account_receivable_id.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'currency_id': currency_id,
            'journal_id': len(journal_ids) and journal_ids[0].id or False,
            'date_invoice': contract.recurring_next_date,
            'origin': contract.code,
            'fiscal_position_id': fpos_id,
            'payment_term_id': partner_payment_term,
            'company_id': contract.company_id.id or False,
            'user_id': self.env.uid or False,
        }
        return invoice

    @api.multi
    def _prepare_invoice_lines(self, contract, fiscal_position_id):
        fpos_obj = self.env['account.fiscal.position']
        fiscal_position = None
        if fiscal_position_id:
            fiscal_position = fpos_obj.browse(fiscal_position_id)
        invoice_lines = []
        for line in contract.recurring_invoice_line_ids:
            values = self._prepare_invoice_line(line, fiscal_position)
            invoice_lines.append((0, 0, values))
        return invoice_lines

    @api.multi
    def _prepare_invoice_line(self, line, fiscal_position):
        fpos_obj = self.env['account.fiscal.position']
        res = line.product_id
        account_id = res.property_account_income_id.id
        if not account_id:
            account_id = res.categ_id.property_account_income_categ_id.id
        account_id = fpos_obj.map_account(account_id)

        taxes = res.taxes_id or False
        values = {
            'name': line.name,
            'account_id': account_id,
            'account_analytic_id': line.analytic_account_id.id,
            'price_unit': line.price_unit or 0.0,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id or False,
            'product_id': line.product_id.id or False,
        }
        if taxes:
            tax_id = fpos_obj.map_tax(taxes)
            values.update({'invoice_line_tax_id': [(6, 0, tax_id)]})
        return values

    @api.multi
    def set_close(self):
        for rec in self:
            return rec.write({'state': 'close'})

    @api.multi
    def set_cancel(self):
        for rec in self:
            return rec.write({'state': 'cancelled'})

    @api.multi
    def set_open(self):
        for rec in self:
            return rec.write({'state': 'open'})

    @api.multi
    def set_pending(self):
        for rec in self:
            return rec.write({'state': 'pending'})
