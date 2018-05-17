# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    current_revision_id = fields.Many2one('purchase.order',
                                          'Current revision',
                                          copy=True,
                                          readonly=True)
    old_revision_ids = fields.One2many('purchase.order',
                                       'current_revision_id',
                                       'Old revisions',
                                       readonly=True,
                                       context={'active_test': False})
    revision_number = fields.Integer('Revision', copy=False)
    old_revision_number = fields.Char('Revision', copy=False)
    is_revision = fields.Boolean('Is Revision')
    unrevisioned_name = fields.Char('Order Reference',
                                    copy=False,
                                    readonly=True)
    active = fields.Boolean('Active',
                            default=True,
                            copy=True)

    _sql_constraints = [
        ('revision_unique',
         'unique(unrevisioned_name, revision_number, company_id)',
         'Order Reference and revision must be unique per Company.'),
    ]

    @api.multi
    def new_revision(self):
        self.ensure_one()
        old_name = self.name
        revno = self.revision_number
        self.write({'name': '%s-%02d' % (self.unrevisioned_name, revno + 1),
                    'revision_number': revno + 1})

        # 'orm.Model.copy' is called instead of 'self.copy' in order to avoid
        # 'purchase.order' method to overwrite our values, like name and state
        defaults = {'name': self.unrevisioned_name,
                    'revision_number': revno,
                    'active': False,
                    'state': 'cancel',
                    'current_revision_id': self.id,
                    'unrevisioned_name': self.unrevisioned_name,
                    'po_company_number': old_name,
                    }
        old_revision = super(PurchaseOrder, self).copy(default=defaults)
        self.write({'po_company_number': old_name,
                    'name': self.po_company_number,
                    'is_revision': True,
                    'old_revision_number': old_name})
        for line_rec in self.order_line:
            line_rec.is_revision = True
        self.button_draft()
        msg = _('New revision created: %s') % self.name
        self.message_post(body=msg)
        old_revision.message_post(body=msg)
        return True

    @api.model
    def create(self, values):
        if 'unrevisioned_name' not in values:
            if values.get('name', '/') == '/':
                seq = self.env['ir.sequence']
                values['name'] = seq.next_by_code('purchase.order') or '/'
            values['unrevisioned_name'] = values['name']
        return super(PurchaseOrder, self).create(values)

    @api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(_(
                        'Unable to cancel purchase order %s as some'
                        ' receptions have already been done.') % (order.name))
            # for inv in order.invoice_ids:
            #     if inv and inv.state not in ('cancel', 'draft'):
            #         raise UserError(_(
            #             "Unable to cancel this purchase order. You must"
            #             " first cancel related vendor bills."))

            for pick in order.picking_ids.filtered(
                    lambda r: r.state != 'cancel'):
                pick.action_cancel()
            # TDE FIXME: I don' think context key is necessary, as actions
            #  are not related / called from each other
            if not self.env.context.get('cancel_procurement'):
                procurements = order.order_line.mapped('procurement_ids')
                procurements.filtered(lambda r: r.state not in ('cancel',
                                      'exception')and r.rule_id.propagate)\
                    .write({'state': 'cancel'})
                procurements.filtered(lambda r: r.state not in ('cancel',
                                      'exception')and not r.rule_id.propagate
                                      ).write({'state': 'exception'})
                moves = procurements.filtered(
                    lambda r: r.rule_id.propagate).mapped('move_dest_id')
                moves.filtered(lambda r: r.state != 'cancel').action_cancel()

        self.write({'state': 'cancel'})


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_revision = fields.Boolean('Is Revision')
