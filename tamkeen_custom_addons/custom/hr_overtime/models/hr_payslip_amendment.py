from odoo import models, fields, api


class HrPayslipAmendment(models.Model):
    _inherit = 'hr.payslip.amendment'

    overtime_request_id = fields.Many2one('overtime.statement.request',
                                          string='Overtime')

    @api.multi
    def do_validate(self):
        res = super(HrPayslipAmendment, self).do_validate()
        for rec in self:
            if rec.overtime_request_id:
                rec.overtime_request_id.service_validate13()
        return res
