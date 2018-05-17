# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning


class MilestonesSchedule(models.Model):
    _name = 'milestones.schedule'

    @api.depends('certificate_of_completion_line_ids'
                 '.certificate_of_completion_id.state')
    def _compute_percentage_completion(self):
        """
        percentage_completion and milestone_achieved update based on related
        certificate record state(po line update qty of invoiced)
        :return:
        """
        for rec in self:
            percentage_completion = 0.0
            milestone_achieved = False
            for coc_line in rec.certificate_of_completion_line_ids:
                if coc_line.certificate_of_completion_id.state not in \
                        ['draft', 'rejected', 'cancelled']:
                    percentage_completion += \
                        (coc_line.rem_percentage *
                         coc_line.accepted_percentage) / 100
                    if coc_line.make_it_as_final_line:
                        milestone_achieved = True
            rec.percentage_completion = percentage_completion
            rec.milestone_achieved = milestone_achieved

    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    name = fields.Char('Action')
    description = fields.Text('Remarks')
    amount = fields.Float('Amount')
    percentage = fields.Float('Percentage')
    percentage_completion = fields.Float(
        'Percentage Completion', compute=_compute_percentage_completion,
        store=True)
    milestone_achieved = fields.Boolean('Milestone Achieved',
                                        compute=_compute_percentage_completion,
                                        store=True)
    certificate_of_completion_line_ids = fields.One2many(
        'certificate.of.completion.line', 'name',
        string='Certificate of Completion Lines')

    @api.multi
    def get_remaining_amount_percentage(self):
        """
        :return:
        """
        rem_amount = 0.0
        rem_per = self.percentage - self.percentage_completion
        if rem_per == 0:
            return 0.0, 0.0
        if not self.percentage_completion:
            return self.amount, self.percentage
        if self.amount and rem_per and self.percentage:
            rem_amount = (self.amount * rem_per) / self.percentage
        return rem_amount, rem_per

    @api.multi
    def name_get(self):
        res = []
        for milestones_rec in self:
            rem_amount, rem_per = \
                milestones_rec.get_remaining_amount_percentage()
            name = milestones_rec.name + ' ( ' + str(rem_per) + '% ,' \
                   + str(rem_amount) + ' )'
            res.append((milestones_rec.id, name))
        return res

    @api.constrains('percentage')
    def check_percentage(self):
        """
        :return:
        """
        for rec in self:
            if rec.percentage < 1 or rec.percentage > 100:
                raise Warning(_('Milestones Percentage should be in between '
                                '1 to 100 !'))

    @api.onchange('percentage')
    def onchange_percentage(self):
        """
        onchange of percentage count amount.
        :return:
        """
        amount = 0.00
        if self.percentage and self.purchase_order_id:
            if self.purchase_order_id.amount_total:
                amount = (self.purchase_order_id.amount_total *
                          self.percentage) / 100
        self.amount = amount

    @api.onchange('amount')
    def onchange_amount(self):
        """
        onchange of amount calculate percentage
        :return:
        """
        percentage = 0.00
        if self.amount and self.purchase_order_id:
            if self.purchase_order_id.amount_total:
                percentage = \
                    (self.amount * 100) / self.purchase_order_id.amount_total
        self.percentage = percentage
