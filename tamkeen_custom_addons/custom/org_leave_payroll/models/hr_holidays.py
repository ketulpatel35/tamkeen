# -*- coding:utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT


# class HrHolidays(models.Model):
#     _inherit = 'hr.holidays'
#
#     payroll_period_state = fields.Selection(
#         [('unlocked', 'Unlocked'), ('locked', 'Locked')],
#         string='Payroll Period State', readonly=True, default='unlocked')
#     payroll_period_id = fields.Many2one('hr.payroll.period',
#                                         string='Payroll Period')
#
#     def _get_payroll_period(self, date):
#         payroll_period_obj = self.env['hr.payroll.period']
#         first_date_of_month = date.replace(day=1)
#         lastMonth_date = first_date_of_month - timedelta(days=1)
#         latest_payroll_period_id = payroll_period_obj.search([
#             ('state', 'in', ('open', 'ended')), ('date_start', '>=',
#                                                  str(lastMonth_date))],
#             order="date_start",
#             limit=1)
#         return latest_payroll_period_id
#
#     @api.multi
#     def holidays_to_manager(self):
#         res = super(HrHolidays, self).holidays_to_manager()
#         for rec in self:
#             date_from = str(rec.date_from).replace(
#                 str(rec.submit_date.split(
#                     ' ')[1]), '00:00:00')
#             date = datetime.strptime(date_from, OE_DATETIMEFORMAT)
#             payroll_period = rec._get_payroll_period(date)
#             rec.write({'payroll_period_id': payroll_period.id})
#         return res
#
#     @api.multi
#     def unlink(self):
#         for holiday in self:
#             if holiday.holiday_status_id and \
#                     holiday.holiday_status_id.ignore_locked_period:
#                 ignore_locked_period = \
#                     holiday.holiday_status_id.ignore_locked_period
#                 if holiday.payroll_period_state == 'locked' and \
#                     holiday.state != 'validate' and not \
#                         ignore_locked_period:
#                     raise Warning(_(
#                         'You cannot delete a leave request which exist in a '
#                         'locked payroll period. \n Please, '
#                         'contact the HR department.'))
#         return super(HrHolidays, self).unlink()
#
#     @api.multi
#     def write(self, vals):
#         for holiday in self:
#             if holiday.holiday_status_id and \
#                     holiday.holiday_status_id.ignore_locked_period:
#                 ignore_locked_period = holiday.holiday_status_id.\
#                     ignore_locked_period
#                 if holiday.payroll_period_state == 'locked' and not vals.get(
#                         'payroll_period_state',
#                         False) and not ignore_locked_period:
#                     raise Warning(_(
#                         'You cannot modify a leave request which exist in a '
#                         'locked payroll period. \n Please, contact the HR '
#                         'department.'))
#         return super(HrHolidays, self).write(vals)