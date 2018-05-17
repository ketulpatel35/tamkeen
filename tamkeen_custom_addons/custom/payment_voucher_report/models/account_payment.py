from odoo import models, api


class AccountPayment(models.Model):
    """Account Payment"""
    _inherit = 'account.payment'

    @api.model
    def get_payment_move_line(self):
        """
        Get Move Line ids and return List of Record set.
        :return:
        """
        acc_move_list = []
        for acc_move_line_rec in self.env['account.move.line'].search(
                [('payment_id', 'in', self.ids)]):
            if acc_move_line_rec.move_id not in acc_move_list:
                acc_move_list.append(acc_move_line_rec.move_id)
        return acc_move_list
