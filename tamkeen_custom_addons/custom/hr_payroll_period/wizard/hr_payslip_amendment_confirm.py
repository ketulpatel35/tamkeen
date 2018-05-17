# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class HrPayslipAmendmentConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft amendment
    """
    _name = "hr.payslip.amendment.confirm"

    @api.multi
    def payslip_amendment_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        pay_period_list = []
        amendment_rec = self.env['hr.payslip.amendment'].browse(active_ids)
        [pay_period_list.append(ame_rec.pay_period_id) for ame_rec in
         amendment_rec if ame_rec.pay_period_id not in pay_period_list]
        if len(pay_period_list) > 1:
            raise UserError(_("Some of the selected amendments are not in the "
                              "same payroll period."
                              ))
        for rec in amendment_rec:
            if rec.state != 'draft':
                raise UserError(_("Some of the selected amendments are not in "
                                  "the "
                              "'Draft' state."))
            rec.do_validate()
        return {'type': 'ir.actions.act_window_close'}