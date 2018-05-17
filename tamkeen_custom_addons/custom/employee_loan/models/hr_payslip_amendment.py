from odoo import models, fields, api, _
from odoo.exceptions import Warning

class HrPayslipAmendment(models.Model):
    _inherit = 'hr.payslip.amendment'

    loan_installment_id = fields.Many2one('loan.installments', string='Loan')

    @api.multi
    def do_done(self):
        """
        when payslip amendment done then installment also done.
        :return:
        """
        res = super(HrPayslipAmendment, self).do_done()
        for rec in self:
            if rec.loan_installment_id:
                rec.loan_installment_id.write({'state': 'done'})
                # when all installment done then Loan also in done state.
                rec.loan_installment_id.loan_id.check_installment_done()
        return res

    @api.multi
    def unlink(self):
        """
        We override unlink method for check if payslip amendment link with
        loan ... he/she cannot delete this amendment.
        :return:super
        """
        for rec in self:
            if rec.loan_installment_id:
                raise Warning(
                    _("You are not allowed to delete this amendment since "
                      "it's linked to another requests.")
                )
            else:
                super(HrPayslipAmendment, rec).unlink()
