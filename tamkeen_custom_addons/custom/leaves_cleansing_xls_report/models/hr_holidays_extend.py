from odoo import models, api, _
import math
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'



    # @api.multi
    # def _get_employee_accural_policy(self, employee_id, holiday_status_id):
    #     """
    #
    #     :param employee_id:
    #     :return:
    #     """
    #     if self._context and self._context.get('holiday_status_rec'):
    #         accrual_line_policy = None
    #         employee_rec = employee_id
    #         if employee_rec and employee_rec.contract_id and \
    #                 employee_rec.contract_id.policy_group_id:
    #             policy_group_rec = employee_rec.contract_id.policy_group_id
    #             for accrual_rec in policy_group_rec.accr_policy_ids:
    #                 for accrual_line_rec in accrual_rec.line_ids:
    #                     accrual_rec = accrual_line_rec.accrual_id
    #                     if accrual_rec and accrual_rec.holiday_status_id:
    #                         if accrual_rec.holiday_status_id.id == \
    #                                 self._context.get(
    #                                     'holiday_status_rec').id:
    #                             accrual_line_policy = accrual_line_rec
    #         return accrual_line_policy
    #     else:
    #         return super(HrHolidays, self)._get_employee_accural_policy(
    #             employee_id, holiday_status_id)
