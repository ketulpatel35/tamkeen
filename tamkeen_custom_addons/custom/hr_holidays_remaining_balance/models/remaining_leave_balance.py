# -*- coding: utf-8 -*-
##############################################################################
from odoo import fields, models, api


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _get_leave_remaining_balance(self):
        """
        :return:
        """
        for rec in self:
            holidays_status_rec = self.env['hr.holidays.status'].search(
                [('code', '=', 'ANNLV')])
            if holidays_status_rec and rec.employee_id:
                leave_balance = \
                    self.env['hr.holidays'].check_for_preliminary_leave(
                        holidays_status_rec, rec.employee_id)
                rec.leave_balance = leave_balance

    leave_balance = fields.Integer(string='Remaining Leave Balance',
                                   help='Remaining annual leave balance',
                                   compute='_get_leave_remaining_balance',
                                   index=True)
