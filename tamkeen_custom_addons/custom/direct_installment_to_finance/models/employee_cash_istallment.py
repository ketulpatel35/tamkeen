from odoo import models, api,fields, _
from odoo.exceptions import Warning


class LoanInstallments(models.Model):
    _inherit = 'loan.installments'

    dont_affect_into_payroll = fields.Boolean(string="Dont't Generate a "
                                                     "Payroll Entry")


    justification = fields.Text(string='Justification')

    @api.multi
    def paid_to_cash(self):
        for rec in self:
            if not rec.dont_affect_into_payroll:
                raise Warning(_("To Proceed, Kindly press on the 'Don\'t "
                                "Generate a Payroll Entry' Check Box."))
            else:
                rec.write({'state': 'finance_processing'})
                self._send_email('loan_inst_req_send_to_finance',
                                 False, rec.id)

    @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].for_xml_id('account',
                                                           'action_move_journal_line')
        # DO NOT FORWARD-PORT
        res['context'] = {}
        return res

    @api.multi
    def mark_as_done(self):
        for rec in self:
            rec.write({'state': 'done'})
            rec.loan_id.check_installment_done()