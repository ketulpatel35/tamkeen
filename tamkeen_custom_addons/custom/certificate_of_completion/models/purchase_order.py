# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('milestones_schedule_ids')
    def _compute_total_percentage(self):
        """
        Compute total percentage
        :return:
        """
        for rec in self:
            percentage = 0.00
            for po_deli_rec in rec.milestones_schedule_ids:
                percentage += po_deli_rec.percentage
            rec.total_percentage = percentage

    @api.constrains('total_percentage')
    def check_total_percentage(self):
        for rec in self:
            if rec.total_percentage > 100:
                raise ValidationError(_('Total Milestone Percentage should '
                                        'not be Greater then 100(%)'))

    def _compute_coc(self):
        """
        count certificate_of_completion_ids
        :return:
        """
        for rec in self:
            rec.coc_count = len(rec.certificate_of_completion_ids)

    milestones_schedule_ids = fields.One2many('milestones.schedule',
                                      'purchase_order_id', 'Delivery Details')
    total_percentage = fields.Float(compute='_compute_total_percentage',
                                    string='Total Percentage', store=True)
    certificate_of_completion_ids = fields.One2many(
        'certificate.of.completion', 'purchase_order_id',
        string='Certificate Of Completion')
    coc_count = fields.Char(compute="_compute_coc", string='# of Bills')

    @api.multi
    def action_view_certificate_of_completion(self):
        """
        This function returns an action that display existing coc of given
        purchase order.
        When only one found, show the coc immediately.
        :return:
        """
        result = {}
        ctx = self._context.copy()
        # override the context to get default data
        cc_id = self.cost_centre_id and self.cost_centre_id.id or False
        ctx.update({'default_purchase_order_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'default_cost_center_id': cc_id,
                    'default_payment_term_id': self.payment_term_id.id,
                    'default_notes': self.notes,})
        tree_view_rec = self.env.ref(
            'certificate_of_completion.certificate_of_completion_tree_view',
            False)
        form_view_rec = self.env.ref(
            'certificate_of_completion.certificate_of_completion_form_view',
            False)
        print 'certificate_o\n\n\nf_completion_tree_view',form_view_rec,tree_view_rec
        result.update({
            'name': _('Certificate of Completion'),
            'res_model': 'certificate.of.completion',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(tree_view_rec.id, 'tree'), (form_view_rec.id, 'form')],
            'domain': "[('id', 'in', " + str(
                self.certificate_of_completion_ids.ids) + ")]",
            'context': ctx,
        })
        # choose the view_mode accordingly
        # if len(self.certificate_of_completion_ids) == 1:
        #     res = self.env.ref('certificate_of_completion'
        #                        '.certificate_of_completion_form_view', False)
        #     result['views'] = [(res and res.id or False, 'form')]
        #     result['res_id'] = self.certificate_of_completion_ids[0].id
        return result

    @api.multi
    def action_view_po_related_payments(self):
        """
        view Purchase Order Related Payments
        :return:
        """
        move_ids = []
        for inv_rec in self.invoice_ids:
            if inv_rec.move_id and inv_rec.state == 'paid':
                if inv_rec.move_id.id not in move_ids:
                    move_ids.append(inv_rec.move_id.id)

        result = {}
        ctx = self._context.copy()
        result.update({
            'name': _('Payments'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': "[('id', 'in', " + str(move_ids) + ")]",
            'context': ctx,
        })
        return result

    @api.multi
    def coc_outstanding_amount_difference(self):
        """
        get outstanding amount difference for report
        :return:
        """
        for rec in self:
            actual_paid = 0.0
            for milestone_rec in rec.milestones_schedule_ids:
                if milestone_rec.milestone_achieved:
                    actual_paid += milestone_rec.amount
            return actual_paid