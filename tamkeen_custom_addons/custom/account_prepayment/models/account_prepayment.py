# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
from datetime import datetime, date
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from calendar import monthrange
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class AccountPrePaymentType(models.Model):
    _name = 'account.prepayment.type'

    name = fields.Char('Name')
    type = fields.Selection([('revenue', 'Revenue'),
                             ('expense', 'Expense')], 'Prepaid Type',
                            default='revenue')
    prepaid_account_id = fields.Many2one('account.account', string='Prepaid Account')
    entry_account_id = fields.Many2one('account.account',
                                       string='Entry : Prepaid Account')
    account_id = fields.Many2one('account.account', 'Entry: Revenue/Expense Account')
    amount = fields.Float('Prepaid Amount')
    no_of_entries = fields.Integer('No of Entries')
    months = fields.Integer('One Entry Every (Months)', default=1)
    journal_id = fields.Many2one('account.journal', 'Journal')
    auto_post = fields.Boolean('Post Journal Entries')
    auto_generate_entry = fields.Boolean('Auto Generate Journal Entry')

    @api.one
    @api.constrains('months')
    def _check_months(self):
        if self.months <= 0:
            raise ValidationError(_('One Entry Every (Months) should be greater than 0!'))


class AccountPrePayment(models.Model):
    _name = 'account.prepayment'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('prepayment_line_ids.move_id')
    def _entry_count(self):
        for prepayment in self:
            res = self.env['account.prepayment.line']. \
                search_count([('account_prepayment_id', '=', prepayment.id),
                              ('move_id', '!=', False)])
            prepayment.entry_count = res or 0

    @api.one
    @api.depends('value', 'prepayment_line_ids.move_check', 'prepayment_line_ids.amount')
    def _amount_residual(self):
        total_amount = 0.0
        for line in self.prepayment_line_ids:
            if line.move_check:
                total_amount += line.amount
        self.value_residual = self.value - total_amount

    name = fields.Char('Sequence', readonly=True, copy=False)
    entry_count = fields.Integer(compute='_entry_count', string='# Journal Entries',
                                 readonly=True, states={'draft': [('readonly', False)]})
    prepayment_type_id = fields.Many2one('account.prepayment.type',
                                         'PrePayment Type',
                                         readonly=True, states={'draft': [('readonly', False)]})
    prepayment_type = fields.Selection(related='prepayment_type_id.type', string='Prepayment Type',
                                       readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Transaction Date', readonly=True, states={'draft': [('readonly', False)]})
    start_date = fields.Date('Start Date', readonly=True, states={'draft': [('readonly', False)]})
    invoice_id = fields.Many2one('account.invoice', 'Invoice', readonly=True, states={'draft': [('readonly', False)]})
    prepayment_line_ids = fields.One2many('account.prepayment.line',
                                          'account_prepayment_id',
                                          'Lines')
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('to_be_closed', 'To Be Closed'),
                              ('closed', 'Closed'),
                              ('done', 'Done')], 'Status', default='draft', readonly=True)
    no_of_entries = fields.Integer(string='No of Entries',
                                   readonly=True, states={'draft': [('readonly', False)]})
    months = fields.Integer(string='One Entry Every (Months)', default=1,
                            readonly=True, states={'draft': [('readonly', False)]})
    value = fields.Float('Total Amount',
                         readonly=True, states={'draft': [('readonly', False)]})
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          readonly=True, states={'draft': [('readonly', False)]})
    entry_account_id = fields.Many2one('account.account',
                                       string='Entry : Prepaid Account',
                                       readonly=True, states={'draft': [('readonly', False)]})
    account_id = fields.Many2one('account.account', 
                                 'Entry: Revenue/Expense Account',
                                 readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 readonly=True, states={'draft': [('readonly', False)]})
    value_residual = fields.Float(compute='_amount_residual', method=True, digits=0, string='Residual Value')
    end_date = fields.Date('End Date')
    reference = fields.Char('Reference', readonly=True,
                            states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Customer/Vendor', readonly=True, states={'draft': [('readonly', False)]})
    partner_reference = fields.Char('Partner Reference', readonly=True, states={'draft': [('readonly', False)]})
    product_id = fields.Many2one('product.product', 'Product', readonly=True, states={'draft': [('readonly', False)]})
    auto_generate_entry = fields.Boolean('Auto Generate Journal Entry')

    @api.one
    @api.constrains('months')
    def _check_months(self):
        if self.months <= 0:
            raise ValidationError(_('One Entry Every (Months) should be greater than 0!'))

    @api.model
    def create(self, vals):
        """
        ovride create method
        :param vals: dictonary
        :return:
        """
        prepayment_type_obj = self.env['account.prepayment.type']
        if vals.get('prepayment_type_id') and not vals.get('name'):
            code = 'deferred.revenue'
            prepayment_type_rec = prepayment_type_obj.browse(vals['prepayment_type_id'])
            if prepayment_type_rec and prepayment_type_rec.type == 'expense':
                code = 'prepaid.expense'
            vals['name'] = self.env['ir.sequence'].next_by_code(code)
        return super(AccountPrePayment, self).create(vals)

    @api.multi
    def unlink(self):
        for prepayment in self:
            if prepayment.state not in ['draft']:
                raise ValidationError(_('You cannot delete a document is in %s state.') % (prepayment.state,))
            for line in prepayment.prepayment_line_ids:
                if line.move_id:
                    raise ValidationError(_('You cannot delete a document that contains posted entries.'))
        return super(AccountPrePayment, self).unlink()

    @api.onchange('prepayment_type_id')
    def onchange_prepayment_type(self):
        self.no_of_entries = 0
        self.months = 0
        if self.prepayment_type_id:
            self.no_of_entries = self.prepayment_type_id.no_of_entries
            self.months = self.prepayment_type_id.months
            self.entry_account_id = self.prepayment_type_id.entry_account_id\
                and self.prepayment_type_id.entry_account_id.id or False
            self.account_id = self.prepayment_type_id.account_id\
                and self.prepayment_type_id.account_id.id or False
            self.journal_id = self.prepayment_type_id.journal_id\
                and self.prepayment_type_id.journal_id.id or False
            self.auto_generate_entry = self.prepayment_type_id.auto_generate_entry

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        self.product_id = False
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id and\
                self.invoice_id.partner_id.id
            self.journal_id = self.invoice_id.journal_id and\
                self.invoice_id.journal_id.id
            self.reference = self.invoice_id.origin and\
                self.invoice_id.origin or self.reference
            self.partner_reference = self.invoice_id.reference and \
                self.invoice_id.reference or self.partner_reference

    @api.multi
    def set_to_running(self):
        return self.write({'state': 'running'})

    @api.multi
    def set_draft(self):
        for rec in self:
            for line in rec.prepayment_line_ids:
                if line.move_id and line.move_id.state == 'posted':
                    line.move_id.button_cancel()
        return self.write({'state': 'draft'})

    @api.multi
    def set_confirm(self):
        for rec in self:
            if not rec.prepayment_line_ids:
                raise ValidationError(_('PrePayment Lines are not generated!'))
            fields = [
                'no_of_entries',
                'months',
                'end_date',
                'invoice_id',
            ]
            ref_tracked_fields = self.env['account.prepayment'].fields_get(fields)
            for prepayment in self:
                tracked_fields = ref_tracked_fields.copy()
                dummy, tracking_value_ids = prepayment._message_track(tracked_fields, dict.fromkeys(fields))
                if prepayment.prepayment_type == 'expense':
                    prepayment.message_post(subject=_('PrePaid Expense created.'), tracking_value_ids=tracking_value_ids)
                else:
                    prepayment.message_post(subject=_('Deferred Revenue created.'), tracking_value_ids=tracking_value_ids)
        return self.write({'state': 'running'})

    @api.multi
    def to_be_closed(self):
        return self.write({'state': 'to_be_closed'})

    @api.multi
    def generate_schedule(self):
        prepayment_line_obj = self.env['account.prepayment.line']
        for prepayment_rec in self:
            self._cr.execute("delete from account_prepayment_line where account_prepayment_id=%s" % prepayment_rec.id)
            no_of_lines = prepayment_rec.no_of_entries
            month_gap = prepayment_rec.months
            total_amount = prepayment_rec.value
            amount = float(total_amount / no_of_lines)
            cumulative = 0.0
            balance = total_amount
            last_bill_date = False
            final_days = 0
            sequence = 1
            remaining_days = 0
            divide_days = 1
            for count in range(0, no_of_lines):
                prepayment_line_vals = {
                    'account_prepayment_id': prepayment_rec.id,
                }
                bill_date = datetime.strptime(prepayment_rec.start_date, DEFAULT_SERVER_DATE_FORMAT)
                flag = True
                if not count:
                    if int(bill_date.strftime('%d')) != 1:
                        total_days = monthrange(int(bill_date.strftime('%d')),
                                                int(bill_date.strftime('%m')))
                        divide_days = total_days[1]
                        remaining_days = divide_days - int(bill_date.strftime('%d'))
                        final_days = divide_days - remaining_days
                        temp_amount = float((amount / divide_days)) * remaining_days
                        cumulative += temp_amount
                        balance = total_amount - cumulative
                        prepayment_line_vals.update({
                            'date': bill_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            'amount': temp_amount
                        })
                        flag = False
                if flag:
                    bill_date = bill_date + relativedelta.relativedelta(
                        months=month_gap * count)
                    bill_date = bill_date.replace(day=1)
                    prepayment_line_vals.update({
                        'date': bill_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'amount': amount
                    })
                    cumulative += amount
                    balance = total_amount - cumulative
                last_bill_date = bill_date
                prepayment_line_vals.update({
                    'balance': balance,
                    'cumulative': cumulative,
                    'sequence': sequence
                })
                sequence += 1
                prepayment_line_obj.create(prepayment_line_vals)
            if final_days:
                bill_date = last_bill_date + relativedelta.relativedelta(months=month_gap)
                bill_date = bill_date.replace(day=1)
                temp_amount = float((amount / divide_days)) * final_days
                cumulative += temp_amount
                balance = total_amount - cumulative
                prepayment_line_obj.create({
                    'account_prepayment_id': prepayment_rec.id,
                    'date': bill_date,
                    'cumulative': cumulative,
                    'amount': temp_amount,
                    'balance': balance,
                    'sequence': sequence
                })
            prepayment_rec.write({'end_date': bill_date})

    @api.multi
    def open_entries(self):
        move_ids = []
        for prepayment in self:
            for line in prepayment.prepayment_line_ids:
                if line.move_id:
                    move_ids.append(line.move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

    @api.multi
    def set_to_close(self):
        move_ids = []
        for prepayment in self:
            unposted_prepayment_line_ids = prepayment.prepayment_line_ids.filtered(lambda x: not x.move_check)
            if unposted_prepayment_line_ids:
                old_values = {
                    'no_of_entries': prepayment.no_of_entries,
                    'end_date': prepayment.end_date
                }
                commands = [(2, line_id.id, False) for line_id in unposted_prepayment_line_ids]

                sequence = len(prepayment.prepayment_line_ids) - len(unposted_prepayment_line_ids) + 1
                vals = {
                    'account_prepayment_id': prepayment.id,
                    'sequence': sequence,
                    'cumulative': prepayment.value,
                    'amount': prepayment.value_residual,
                    'balance': 0,
                    'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                }
                commands.append((0, False, vals))
                prepayment.write({'prepayment_line_ids': commands, 'no_of_entries': sequence,
                                  'end_date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)})
                tracked_fields = self.env['account.prepayment'].fields_get(['no_of_entries', 'end_date'])
                changes, tracking_value_ids = prepayment._message_track(tracked_fields, old_values)
                if changes:
                    if prepayment.prepayment_type == 'expense':
                        prepayment.message_post(subject=_('PrePaid Expense is closed'), tracking_value_ids=tracking_value_ids)
                    else:
                        prepayment.message_post(subject=_('Deferred Revenue is closed'), tracking_value_ids=tracking_value_ids)
                move_ids += prepayment.prepayment_line_ids[-1].create_move(post_move=True)
        if move_ids:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(move_ids) > 1:
                name = _('Disposal Moves')
                view_mode = 'tree,form'
            return {
                'name': name,
                'view_type': 'form',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': move_ids[0],
            }

    @api.multi
    def write(self, vals):
        res = True
        for rec in self:
            old_values = {
                'account_analytic_id': rec.account_analytic_id,
                'value': rec.value
            }
            res = super(AccountPrePayment, rec).write(vals)
            tracked_fields = self.env['account.prepayment'].fields_get(['account_analytic_id', 'value'])
            changes, tracking_value_ids = rec._message_track(tracked_fields, old_values)
            if changes:
                if rec.prepayment_type == 'expense':
                    rec.message_post(subject=_('PrePaid Expense Updated.'), tracking_value_ids=tracking_value_ids)
                else:
                    rec.message_post(subject=_('Deferred Revenue Updated.'), tracking_value_ids=tracking_value_ids)
        return res

    @api.model
    def generate_automatic_entry(self):
        current_date = date.today()
        last_day = monthrange(current_date.year, current_date.month)
        if last_day and last_day[1] and str(last_day[1]) == str(datetime.now().strftime('%d')):
            prepayment_recs = self.env['account.prepayment'].search([('auto_generate_entry', '=', True),
                                                                     ('state', '=', 'running')])
            for prepayment_rec in prepayment_recs:
                for prepayment_line in prepayment_rec.prepayment_line_ids:
                    if prepayment_line.date <= datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT) and not prepayment_line.move_id:
                        prepayment_line.create_move()
        return True


class AccountPrePaymentLine(models.Model):
    _name = 'account.prepayment.line'

    @api.multi
    @api.depends('move_id')
    def _get_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    @api.multi
    @api.depends('move_id.state')
    def _get_move_posted_check(self):
        for line in self:
            line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

    @api.multi
    @api.depends('move_id', 'move_id.state')
    def _get_line_state(self):
        for line in self:
            line.state = 'pending'
            if line.move_id:
                line.state = line.move_id.state == 'draft' and 'created' or 'done' 

    account_prepayment_id = fields.Many2one('account.prepayment', ondelete="cascade")
    sequence = fields.Integer('Sequence')
    date = fields.Date('Date')
    balance = fields.Float('Balance')
    amount = fields.Float('Amount')
    cumulative = fields.Float('Cumulative')
    parent_state = fields.Selection(related='account_prepayment_id.state', string='State of Prepayment')
    move_id = fields.Many2one('account.move', string='Journal Entry')
    move_check = fields.Boolean(compute='_get_move_check', string='Linked', track_visibility='always', store=True)
    move_posted_check = fields.Boolean(compute='_get_move_posted_check', string='Posted', track_visibility='always', store=True)
    state = fields.Selection(compute='_get_line_state', selection=[('pending', 'Pending'), ('created', 'Entry Created'), ('done', 'Entry Posted')],
                             string="State", default='pending')

    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        for line in self:
            prepayment_rec = line.account_prepayment_id
            journal_id = prepayment_rec.journal_id and \
                prepayment_rec.journal_id.id or False
            account_id = prepayment_rec.account_id and \
                prepayment_rec.account_id.id or False
            entry_account_id = prepayment_rec.entry_account_id and \
                prepayment_rec.entry_account_id.id or False

            if not journal_id:
                journal_id = prepayment_rec.prepayment_type_id \
                    and prepayment_rec.prepayment_type_id.journal_id \
                    and prepayment_rec.prepayment_type_id.journal_id.id \
                    or False
            if not account_id:
                account_id = prepayment_rec.prepayment_type_id \
                    and prepayment_rec.prepayment_type_id.account_id \
                    and prepayment_rec.prepayment_type_id.account_id.id \
                    or False
            if not entry_account_id:
                entry_account_id = prepayment_rec.prepayment_type_id \
                    and prepayment_rec.prepayment_type_id.entry_account_id \
                    and prepayment_rec.prepayment_type_id.entry_account_id.id \
                    or False
            name = ''
            if line.account_prepayment_id.reference:
                name += line.account_prepayment_id.reference
                name += " - "
            if line.account_prepayment_id.partner_reference:
                name += line.account_prepayment_id.partner_reference
                name += " - "
            name += line.account_prepayment_id.name + ' (%s/%s)' % \
                (line.sequence,
                 len(line.account_prepayment_id.prepayment_line_ids))
            amount = line.amount
            prec = self.env['decimal.precision'].precision_get('Account')

            amount = amount * (prepayment_rec.prepayment_type_id.type in ('expense') and 1 or -1)
            move_line_1 = {
                'name': name,
                'account_id': entry_account_id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': journal_id,
                'partner_id': prepayment_rec.partner_id and prepayment_rec.partner_id.id or False,
                'analytic_account_id': prepayment_rec.account_analytic_id.id and prepayment_rec.account_analytic_id.id or False,
                'product_id': prepayment_rec.product_id.id if prepayment_rec.prepayment_type_id.type == 'revenue' else False,
            }
            move_line_2 = {
                'name': name,
                'account_id': account_id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': journal_id,
                'partner_id': prepayment_rec.partner_id and prepayment_rec.partner_id.id or False,
                'analytic_account_id': prepayment_rec.account_analytic_id.id and prepayment_rec.account_analytic_id.id or False,
                'product_id': prepayment_rec.product_id.id if prepayment_rec.prepayment_type_id.type == 'expense' else False,
            }
            move_vals = {
                'ref': line.account_prepayment_id.name,
                'date': line.date,
                'journal_id': journal_id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            }
            move = self.env['account.move'].create(move_vals)
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move
        if post_move and created_moves:
            created_moves.filtered(lambda m: any(m.prepeyment_line_ids.mapped('account_prepayment_id.prepayment_type_id.auto_post'))).post()
        return [x.id for x in created_moves]

    @api.multi
    def post_lines_and_close_asset(self):
        # we re-evaluate the assets to determine whether we can close them
        for line in self:
            prepayment_rec = line.account_prepayment_id
            if not prepayment_rec.value_residual:
                prepayment_rec.write({'state': 'closed'})


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        context = dict(self._context)
        if context is None:
            context = {}
        if context.get('prepayment_invoice_id', False):
            invoice_line_recs = self.env['account.invoice.line'].search([('invoice_id', '=', context['prepayment_invoice_id'])])
            product_ids = [invoice_line_rec.product_id.id for invoice_line_rec in invoice_line_recs if invoice_line_rec.product_id]
            if product_ids:
                args += [('id', 'in', list(set(product_ids)))]
        return super(ProductProduct, self)._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
