# -*- coding:utf-8 -*-
from pytz import timezone, utc
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.exceptions import Warning
import calendar


class last_X_days:
    """Last X Days
    Keeps track of the days an employee worked/didn't work in the last X days.
    """

    def __init__(self, days=6):
        self.limit = days
        self.arr = []

    def push(self, worked=False):
        if len(self.arr) == self.limit:
            self.arr.pop(0)
        self.arr.append(worked)
        return [v for v in self.arr]

    def days_worked(self):
        res = 0
        for d in self.arr:
            if d:
                res += 1
        return res


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    # @api.model
    # def _get_policy(self, policy_group, policy_ids, dDay):
    #     """
    #     Return a policy with an effective date before dDay but greater than
    #     all others
    #     :param policy_group: Policy Group id
    #     :param policy_ids: List of Ids
    #     :param dDay: days
    #     :return:
    #     """
    #     if not policy_group or not policy_ids:
    #         return None
    #
    #     res = None
    #     for policy in policy_ids:
    #         dPolicy = datetime.strptime(policy.date, OE_DATEFORMAT).date()
    #         if dPolicy <= dDay:
    #             if res is None:
    #                 res = policy
    #             elif dPolicy > datetime.strptime(res.date,
    #                                              OE_DATEFORMAT).date():
    #                 res = policy
    #     return res

    # @api.model
    # def _get_ot_policy(self, policy_group, dDay):
    #     """
    #     Return an OT policy with an effective date before dDay but greater
    #     than all others
    #     :param policy_group:
    #     :param dDay:
    #     :return:
    #     """
    #     return self._get_policy(policy_group, policy_group.ot_policy_ids, dDay)

    # @api.model
    # def _get_absence_policy(self, policy_group, dDay):
    #     """
    #     Return an Absence policy with an effective date before dDay but
    #     greater than all others
    #     :param policy_group:
    #     :param dDay:
    #     :return:
    #     """
    #     return self._get_policy(policy_group,
    #                             policy_group.absence_policy_ids, dDay)

    # @api.model
    # def _get_presence_policy(self, policy_group, dDay):
    #     """
    #     Return a Presence Policy with an effective date before dDay but
    #     greater than all others
    #     :param policy_group:
    #     :param dDay:
    #     :return:
    #     """
    #     return self._get_policy(policy_group,
    #                             policy_group.presence_policy_ids, dDay)

    # @api.model
    # def _get_applied_time(self, worked_hours, pol_active_after,
    #                       pol_duration=None):
    #     """
    #     Returns worked time in hours according to pol_active_after and
    #     pol_duration.
    #     :param worked_hours: hours
    #     :param pol_active_after:
    #     :param pol_duration: time duration
    #     :return: Number of hours
    #     """
    #     applied_min = (worked_hours * 60) - pol_active_after
    #     if applied_min > 0.01:
    #         applied_min = (pol_duration is not None and applied_min >
    #                        pol_duration) and pol_duration or applied_min
    #     else:
    #         applied_min = 0
    #     applied_hours = float(applied_min) / 60.0
    #     return applied_hours

    # @api.model
    # def _book_holiday_hours(self, contract,
    #                         attendances, holiday_obj,
    #                         dtDay, rest_days, lsd, worked_hours):
    #     """
    #
    #     :param contract: Contract Record
    #     :param presence_policy:
    #     :param ot_policy:
    #     :param attendances:
    #     :param holiday_obj:
    #     :param dtDay:
    #     :param rest_days:
    #     :param lsd:
    #     :param worked_hours:
    #     :return:
    #     """
    #
    #     done = False
    #     push_lsd = True
    #     hours = worked_hours
    #
    #     # Process normal working hours
    #     # for line in presence_policy.line_ids:
    #     #     if line.type == 'holiday':
    #     #         holiday_hours = self._get_applied_time(
    #     #             worked_hours, line.active_after,
    #     #             line.duration)
    #     #         attendances[line.code]['number_of_hours'] += holiday_hours
    #     #         attendances[line.code]['number_of_days'] += 1.0
    #     #         hours -= holiday_hours
    #     #         done = True
    #
    #     # Process OT hours
    #     # for line in ot_policy.line_ids:
    #     #     if line.type == 'holiday':
    #     #         ot_hours = self._get_applied_time(
    #     #             worked_hours, line.active_after)
    #     #         attendances[line.code]['number_of_hours'] += ot_hours
    #     #         attendances[line.code]['number_of_days'] += 1.0
    #     #         hours -= ot_hours
    #     #         done = True
    #
    #     if done and (dtDay.weekday() in rest_days or lsd.days_worked == 6):
    #         # Mark this day as *not* worked so that subsequent days
    #         # are not treated as over-time.
    #         lsd.push(False)
    #         push_lsd = False
    #     if hours > -0.01 and hours < 0.01:
    #         hours = 0
    #     return hours, push_lsd

    # @api.model
    # def _book_restday_hours(self, contract, presence_policy,
    #                         ot_policy, attendances, dtDay,
    #                         rest_days, lsd, worked_hours):
    #     """
    #     :param contract: Contract Records
    #     :param presence_policy:
    #     :param ot_policy:
    #     :param attendances:
    #     :param dtDay:
    #     :param rest_days:
    #     :param lsd:
    #     :param worked_hours:
    #     :return:
    #     """
    #     done = False
    #     push_lsd = True
    #     hours = worked_hours
    #
    #     # Process normal working hours
    #     for line in presence_policy.line_ids:
    #         if line.type == 'restday' and dtDay.weekday() in rest_days:
    #             rd_hours = self._get_applied_time(
    #                 worked_hours, line.active_after, line.duration)
    #             attendances[line.code]['number_of_hours'] += rd_hours
    #             attendances[line.code]['number_of_days'] += 1.0
    #             hours -= rd_hours
    #             done = True
    #
    #     # Process OT hours
    #     for line in ot_policy.line_ids:
    #         if line.type == 'restday' and dtDay.weekday() in rest_days:
    #             ot_hours = self._get_applied_time(
    #                 worked_hours, line.active_after)
    #             attendances[line.code]['number_of_hours'] += ot_hours
    #             attendances[line.code]['number_of_days'] += 1.0
    #             hours -= ot_hours
    #             done = True
    #
    #     if done and (dtDay.weekday() in rest_days or lsd.days_worked == 6):
    #         # Mark this day as *not* worked so that subsequent days
    #         # are not treated as over-time.
    #         lsd.push(False)
    #         push_lsd = False
    #
    #     if hours > -0.01 and hours < 0.01:
    #         hours = 0
    #     return hours, push_lsd

    # @api.model
    # def _book_weekly_restday_hours(
    #         self, contract, presence_policy, ot_policy,
    #         attendances, dtDay, rest_days, lsd, worked_hours):
    #     """
    #     :param contract: Contract Record
    #     :param presence_policy:
    #     :param ot_policy:
    #     :param attendances:
    #     :param dtDay:
    #     :param rest_days:
    #     :param lsd:
    #     :param worked_hours:
    #     :return:
    #     """
    #     done = False
    #     push_lsd = True
    #     hours = worked_hours
    #     # Process normal working hours
    #     # for line in presence_policy.line_ids:
    #     #     if line.type == 'restday':
    #     #         if lsd.days_worked() == line.active_after:
    #     #             rd_hours = self._get_applied_time(
    #     #                 worked_hours, line.active_after, line.duration)
    #     #             attendances[line.code]['number_of_hours'] += rd_hours
    #     #             attendances[line.code]['number_of_days'] += 1.0
    #     #             hours -= rd_hours
    #     #             done = True
    #
    #     # Process OT hours
    #     for line in ot_policy.line_ids:
    #         if line.type == 'weekly' and line.weekly_working_days and \
    #                         line.weekly_working_days > 0:
    #             if lsd.days_worked() == line.weekly_working_days:
    #                 ot_hours = self._get_applied_time(
    #                     worked_hours, line.active_after)
    #                 attendances[line.code]['number_of_hours'] += ot_hours
    #                 attendances[line.code]['number_of_days'] += 1.0
    #                 hours -= ot_hours
    #                 done = True
    #
    #     if done and (dtDay.weekday() in rest_days or lsd.days_worked == 6):
    #         # Mark this day as *not* worked so that subsequent days
    #         # are not treated as over-time.
    #         lsd.push(False)
    #         push_lsd = False
    #
    #     if hours > -0.01 and hours < 0.01:
    #         hours = 0
    #     return hours, push_lsd

    # @api.model
    # def holidays_list_init(self, dFrom, dTo):
    #     """
    #     :param dFrom: Date From
    #     :param dTo: Date To
    #     :return:
    #     """
    #     holiday_obj = self.env['hr.holidays.public']
    #     res = holiday_obj.get_holidays_list(dFrom.year)
    #     if dTo.year != dFrom.year:
    #         res += holiday_obj.get_holidays_list(
    #             dTo.year)
    #     return res
    #
    # @api.model
    # def holidays_list_contains(self, date, holidays_list):
    #     """
    #     :param date: Date
    #     :param holidays_list: Holiday List
    #     :return: Boolean
    #     """
    #     if date.strftime(OE_DATEFORMAT) in holidays_list:
    #         return True
    #     return False

    # @api.model
    # def attendance_dict_init(self, contract, dFrom, dTo):
    #     """
    #     :param contract: Contract Record
    #     :param dFrom: Date From
    #     :param dTo: Date To
    #     :return:
    #     """
    #     att_obj = self.env['hr.attendance']
    #     res = {}
    #     att_list = att_obj.punches_list_init(contract.employee_id.id,
    #                                          contract.pps_id, dFrom,
    #                                          dTo)
    #     res.update({'raw_list': att_list})
    #     d = dFrom
    #     while d <= dTo:
    #         res[d.strftime(
    #             OE_DATEFORMAT)] = att_obj.total_hours_on_day(
    #             contract, d, punches_list=att_list)
    #         d += timedelta(days=+1)
    #     return res

    # @api.model
    # def attendance_dict_hours_on_day(self, date, attendance_dict):
    #     """
    #     :param date: Date
    #     :param attendance_dict:
    #     :return:
    #     """
    #     return attendance_dict[date.strftime(OE_DATEFORMAT)]

    # @api.model
    # def attendance_dict_list(self, att_dict):
    #     """
    #     :param att_dict:
    #     :return:
    #     """
    #     if att_dict.get('raw_list'):
    #         return att_dict['raw_list']
    #     else:
    #         return False

    # @api.model
    # def leaves_list_init(self, employee_id, dFrom, dTo, tz):
    #     """
    #     Returns a list of tuples containing start, end dates for leaves within
    #     the specified period.
    #     :param employee_id: Employee Id
    #     :param dFrom: Date From
    #     :param dTo: Date To
    #     :param tz: Time Zone
    #     :return:
    #     """
    #     leave_obj = self.env['hr.holidays']
    #     dtS = datetime.strptime(
    #         dFrom.strftime(OE_DATEFORMAT) + ' 00:00:00', OE_DATETIMEFORMAT)
    #     dtE = datetime.strptime(
    #         dTo.strftime(OE_DATEFORMAT) + ' 23:59:59', OE_DATETIMEFORMAT)
    #     utcdt_dayS = timezone(tz).localize(dtS).astimezone(utc)
    #
    #     utcdt_dayE = timezone(tz).localize(dtE).astimezone(utc)
    #     utc_dayS = utcdt_dayS.strftime(OE_DATETIMEFORMAT)
    #     utc_dayE = utcdt_dayE.strftime(OE_DATETIMEFORMAT)
    #     leave_ids = leave_obj.search([
    #         ('state', 'in', ['validate', 'leave_approved']),
    #         ('employee_id', '=', employee_id),
    #         ('type', '=', 'remove'),
    #         ('date_from', '<=', utc_dayE),
    #         ('date_to', '>=', utc_dayS)])
    #     res = []
    #     if len(leave_ids) != 0:
    #         for leave in leave_ids:
    #             res.append({
    #                 'code': leave.holiday_status_id.code,
    #                 'tz': tz,
    #                 'start': utc.localize(datetime.strptime(
    #                     leave.date_from, OE_DATETIMEFORMAT)),
    #                 'end': utc.localize(datetime.strptime(leave.date_to,
    #                                                       OE_DATETIMEFORMAT))
    #             })
    #     return res

    # @api.model
    # def leaves_list_get_hours(self, employee_id, contract_id, sched_tpl_id,
    #                           d, leaves_list):
    #     """
    #     Return the number of hours of leave on a given date, d.
    #     :param employee_id: Employee id
    #     :param contract_id: contract id
    #     :param sched_tpl_id:
    #     :param d: Date
    #     :param leaves_list:
    #     :return:
    #     """
    #     code = False
    #     hours = 0
    #     if len(leaves_list) == 0:
    #         return code, hours
    #     dtS = datetime.strptime(
    #         d.strftime(OE_DATEFORMAT) + ' 00:00:00', OE_DATETIMEFORMAT)
    #     dtE = datetime.strptime(
    #         d.strftime(OE_DATEFORMAT) + ' 23:59:59', OE_DATETIMEFORMAT)
    #     for l in leaves_list:
    #         utcBegin = l['start']
    #         utcEnd = l['end']
    #         dtLvBegin = datetime.strptime(
    #             utcBegin.strftime(OE_DATETIMEFORMAT), OE_DATETIMEFORMAT)
    #         dtLvEnd = datetime.strptime(
    #             utcEnd.strftime(OE_DATETIMEFORMAT), OE_DATETIMEFORMAT)
    #         utcdt_dayS = timezone(l['tz']).localize(dtS).astimezone(utc)
    #         utcdt_dayE = timezone(l['tz']).localize(dtE).astimezone(utc)
    #         if utcdt_dayS <= utcEnd and utcdt_dayE >= utcBegin:
    #             code = l['code']
    #             hr_schedule_detail_obj = self.env['hr.schedule.detail']
    #             if utcBegin.date() < utcdt_dayS.date() and utcEnd.date() > \
    #                     utcdt_dayS.date():
    #                 hours = 24
    #             elif utcBegin.date() == utcdt_dayE.date():
    #                 hours = float((utcdt_dayE - utcBegin).seconds / 60) / 60.0
    #             elif utcBegin.date() == utcdt_dayS.date():
    #                 shift_times = \
    #                     hr_schedule_detail_obj.scheduled_begin_end_times(
    #                         employee_id, contract_id, dtS)
    #                 if len(shift_times) > 0:
    #                     for dtStart, dtEnd in shift_times:
    #                         if dtLvBegin < dtEnd:
    #                             dt = (
    #                                 dtLvBegin < dtStart) and dtStart or \
    #                                 dtLvBegin
    #                             hours += float(
    #                                 (dtEnd - dt).seconds / 60) / 60.0
    #                             dtLvBegin = dtEnd
    #                 else:
    #                     hours =\
    #                         sched_tpl_id.get_hours_by_weekday(
    #                             d.weekday()) or 8
    #             else:  # dtTo.date() == dToday
    #                 shift_times = \
    #                     hr_schedule_detail_obj.scheduled_begin_end_times(
    #                         employee_id, contract_id, dtS)
    #                 if len(shift_times) > 0:
    #                     for dtStart, dtEnd in shift_times:
    #                         if dtLvEnd > dtStart:
    #                             dt = (dtLvEnd > dtEnd) and dtEnd or dtLvEnd
    #                             hours += float(
    #                                 (dt - dtStart).seconds / 60) / 60.0
    #                 else:
    #                     hours =\
    #                         sched_tpl_id.get_hours_by_weekday(
    #                             d.weekday()) or 8
    #
    #     return code, hours

    # Copied from addons/hr_payroll so that we can override worked days
    # calculation to
    # handle Overtime and absence
    # @api.model
    # def get_worked_day_lines(self, contract_ids, date_from, date_to):
    #     """
    #     @param contract_ids: list of contract id
    #     @return: returns a list of dict containing the input that should be
    #     applied for the given contract between date_from and date_to
    #     """
    #     # sched_tpl_obj = self.env['hr.schedule.template']
    #     sched_obj = self.env['hr.schedule']
    #     sched_detail_obj = self.env['hr.schedule.detail']
    #     # ot_obj = self.env['hr.policy.ot']
    #     # presence_obj = self.env['hr.policy.presence']
    #     # absence_obj = self.env['hr.policy.absence']
    #     holiday_obj = self.env['hr.holidays.public']
    #
    #     day_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    #     day_to = datetime.strptime(date_to, "%Y-%m-%d").date()
    #     nb_of_days = (day_to - day_from).days + 1
    #
    #     # Initialize list of public holidays. We only need to calculate it
    #     # once during
    #     # the lifetime of this object so attach it directly to it.
    #     #
    #     try:
    #         public_holidays_list = self._mtm_public_holidays_list
    #     except AttributeError:
    #         self._mtm_public_holidays_list = self.holidays_list_init(
    #             day_from, day_to)
    #         public_holidays_list = self._mtm_public_holidays_list
    #
    #     # def get_ot_policies(policy_group_id, day, data):
    #     #
    #     #     if data is None or not data['_reuse']:
    #     #         data = {
    #     #             'policy': None,
    #     #             'daily': None,
    #     #             'restday2': None,
    #     #             'restday': None,
    #     #             'weekly': None,
    #     #             'holiday': None,
    #     #             '_reuse': False,
    #     #         }
    #     #     elif data['_reuse']:
    #     #         return data
    #     #
    #     #     ot_policy = self._get_ot_policy(policy_group_id, day)
    #     #     daily_ot = ot_policy and len(ot_policy.daily_codes()) > 0 or None
    #     #     restday2_ot = ot_policy and len(ot_policy.restday2_codes()) > 0 \
    #     #         or None
    #     #     restday_ot = ot_policy and len(ot_policy.restday_codes()) > 0 \
    #     #         or None
    #     #     weekly_ot = ot_policy and len(ot_policy.weekly_codes()) > 0 or \
    #     #         None
    #     #     holiday_ot = ot_policy and len(ot_policy.holiday_codes()) > 0 \
    #     #         or None
    #     #
    #     #     data['policy'] = ot_policy
    #     #     data['daily'] = daily_ot
    #     #     data['restday2'] = restday2_ot
    #     #     data['restday'] = restday_ot
    #     #     data['weekly'] = weekly_ot
    #     #     data['holiday'] = holiday_ot
    #     #     print data
    #     #     return data
    #
    #     def get_absence_policies(policy_group_id, day, data):
    #         if data is None or not data['_reuse']:
    #             data = {
    #                 'policy': None,
    #                 '_reuse': False,
    #             }
    #         elif data['_reuse']:
    #             return data
    #         absence_policy = self._get_absence_policy(policy_group_id, day)
    #         data['policy'] = absence_policy
    #         return data
    #
    #     # def get_presence_policies(policy_group_id, day, data):
    #     #     if data is None or not data['_reuse']:
    #     #         data = {
    #     #             'policy': None,
    #     #             '_reuse': False,
    #     #         }
    #     #     elif data['_reuse']:
    #     #         return data
    #     #     policy = self._get_presence_policy(policy_group_id, day)
    #     #     data['policy'] = policy
    #     #     return data
    #
    #     res = []
    #     for contract in self.env['hr.contract'].browse(contract_ids):
    #         worked_hours_in_week = 0
    #         # Initialize list of leave's taken by the employee during the month
    #
    #         if not contract.pps_id:
    #             raise Warning(_('Warning !'
    #                             '\nPlease set Payroll Period Schedule for \n'
    #                             'Employee : %s \nContract : %s') % (
    #                 contract.employee_id.name, contract.name))
    #         leaves_list = self.leaves_list_init(contract.employee_id.id,
    #                                             day_from, day_to,
    #                                             contract.pps_id.tz)
    #
    #         # Get default set of rest days for this employee/contract
    #         contract_rest_days = []
    #         if contract.working_hours:
    #             contract_rest_days = \
    #                 contract.working_hours.get_rest_days()
    #         # Initialize dictionary of dates in this payslip and the hours the
    #         # employee was scheduled to work on each
    #         sched_hours_dict = \
    #             sched_detail_obj.scheduled_begin_end_times_range(
    #                 contract.employee_id.id, contract.id, day_from, day_to)
    #         # Initialize dictionary of hours worked per day
    #         working_hours_dict = self.attendance_dict_init(
    #             contract, day_from, day_to)
    #
    #         # Short-circuit:
    #         # If the policy for the first day is the same as the one for the
    #         # last day assume that it will also be the same for the days in
    #         # between, and reuse the same policy instead of checking for
    #         # every day.
    #         # ot_data = None
    #         # data2 = None
    #
    #         # ot_data = get_ot_policies(contract.policy_group_id, day_from,
    #         #                           ot_data)
    #         # data2 = get_ot_policies(contract.policy_group_id, day_to, data2)
    #         # if (ot_data['policy'] and data2['policy']) and ot_data[
    #         #         'policy'].id == data2['policy'].id:
    #         #     ot_data['_reuse'] = True
    #
    #         absence_data = None
    #         data2 = None
    #         absence_data = get_absence_policies(
    #             contract.policy_group_id, day_from, absence_data)
    #         data2 = get_absence_policies(
    #             contract.policy_group_id, day_to, data2)
    #         if (absence_data['policy'] and data2['policy']) and \
    #                 absence_data['policy'].id == data2['policy'].id:
    #             absence_data['_reuse'] = True
    #
    #         # presence_data = None
    #         # data2 = None
    #         # presence_data = get_presence_policies(
    #         #     contract.policy_group_id, day_from, presence_data)
    #         # data2 = get_presence_policies(
    #         #     contract.policy_group_id, day_to, data2)
    #         # if (presence_data['policy'] and data2['policy']) and \
    #         #         presence_data['policy'].id == data2['policy'].id:
    #         #     presence_data['_reuse'] = True
    #
    #         # Calculate the number of days worked in the last week of
    #         # the previous month. Necessary to calculate Weekly Rest Day OT.
    #         #
    #         lsd = last_X_days()
    #         att_obj = self.env['hr.attendance']
    #         if len(lsd.arr) == 0:
    #             d = day_from - timedelta(days=6)
    #             while d < day_from:
    #                 att_ids = att_obj.search([
    #                     ('employee_id', '=', contract.employee_id.id),
    #                     '|', ('check_in', '=', d.strftime(OE_DATEFORMAT)),
    #                     ('check_out', '=', d.strftime(OE_DATEFORMAT))])
    #                 if len(att_ids) > 1:
    #                     lsd.push(True)
    #                 else:
    #                     lsd.push(False)
    #                 d += timedelta(days=1)
    #
    #         attendances = {
    #             'MAX': {
    #                 'name': _("Maximum Possible Working Hours"),
    #                 'sequence': 1,
    #                 'code': 'MAX',
    #                 'number_of_days': 0.0,
    #                 'number_of_hours': 0.0,
    #                 'contract_id': contract.id,
    #             },
    #         }
    #         leaves = {}
    #         # att_obj = self.env['hr.attendance']
    #         awol_code = False
    #         import logging
    #         _l = logging.getLogger(__name__)
    #         for day in range(0, nb_of_days):
    #             dtDateTime = datetime.strptime(
    #                 (day_from + timedelta(days=day)).strftime(OE_DATEFORMAT),
    #                 OE_DATEFORMAT)
    #             rest_days = contract_rest_days
    #             normal_working_hours = 0
    #
    #             # Get Presence data
    #             #
    #             # presence_data = get_presence_policies(
    #             #     contract.policy_group_id, dtDateTime.date(), presence_data)
    #             # presence_policy = presence_data['policy']
    #             # presence_codes = presence_policy and \
    #             #     presence_policy.get_codes() or []
    #             # presence_sequence = 2
    #
    #             # for pcode, pname, ptype, prate, pduration in presence_codes:
    #             #     if attendances.get(pcode, False):
    #             #         continue
    #             #     if ptype == 'normal':
    #             #         normal_working_hours += float(pduration) / 60.0
    #             #     attendances[pcode] = {
    #             #         'name': pname,
    #             #         'code': pcode,
    #             #         'sequence': presence_sequence,
    #             #         'number_of_days': 0.0,
    #             #         'number_of_hours': 0.0,
    #             #         'rate': prate,
    #             #         'contract_id': contract.id,
    #             #     }
    #             #     presence_sequence += 1
    #
    #             # Get OT data
    #             # ot_data = get_ot_policies(
    #             #     contract.policy_group_id, dtDateTime.date(), ot_data)
    #             # ot_policy = ot_data['policy']
    #             # daily_ot = ot_data['daily']
    #             # restday2_ot = ot_data['restday2']
    #             # restday_ot = ot_data['restday']
    #             # weekly_ot = ot_data['weekly']
    #             # ot_codes = ot_policy and ot_policy.get_codes() or []
    #             ot_sequence = 3
    #
    #             # for otcode, otname, ottype, otrate in ot_codes:
    #             #     if attendances.get(otcode, False):
    #             #         continue
    #             #     attendances[otcode] = {
    #             #         'name': otname,
    #             #         'code': otcode,
    #             #         'sequence': ot_sequence,
    #             #         'number_of_days': 0.0,
    #             #         'number_of_hours': 0.0,
    #             #         'rate': otrate,
    #             #         'contract_id': contract.id,
    #             #     }
    #             #     ot_sequence += 1
    #
    #             # Get Absence data
    #             #
    #             absence_data = get_absence_policies(
    #                 contract.policy_group_id, dtDateTime.date(), absence_data)
    #             absence_policy = absence_data['policy']
    #             absence_codes = absence_policy and absence_policy.get_codes(
    #             ) or []
    #             absence_sequence = 50
    #             for abcode, abname, abtype, abrate, useawol in absence_codes:
    #                 if leaves.get(abcode, False):
    #                     continue
    #                 if useawol:
    #                     awol_code = abcode
    #                 if abtype == 'unpaid':
    #                     abrate = 0
    #                 elif abtype == 'dock':
    #                     abrate = -abrate
    #                 leaves[abcode] = {
    #                     'name': abname,
    #                     'code': abcode,
    #                     'sequence': absence_sequence,
    #                     'number_of_days': 0.0,
    #                     'number_of_hours': 0.0,
    #                     'rate': abrate,
    #                     'contract_id': contract.id,
    #                 }
    #                 absence_sequence += 1
    #
    #             # For Leave related computations:
    #             # actual_rest_days: days that are rest days in schedule that
    #             #  was actualy used scheduled_hours: nominal number of
    #             # full-time hours for the working day. If the employee is
    #             # scheduled for this day we use those hours. If not we try
    #             # to determine the hours he/she would have worked based on
    #             # the schedule template attached to the contract.
    #
    #             actual_rest_days = sched_obj.get_rest_days(
    #                 contract.employee_id.id, dtDateTime)
    #             scheduled_hours = \
    #                 sched_detail_obj.scheduled_hours_on_day_from_range(
    #                     dtDateTime.date(), sched_hours_dict)
    #             # If the calculated rest days and actual rest days differ, use
    #             # actual rest days
    #             if actual_rest_days is not None and len(rest_days) != len(
    #                     actual_rest_days):
    #                 rest_days = actual_rest_days
    #             elif actual_rest_days is not None:
    #                 for d in actual_rest_days:
    #                     if d not in rest_days:
    #                         rest_days = actual_rest_days
    #                         break
    #
    #             if scheduled_hours == 0 and dtDateTime.weekday() not in \
    #                     rest_days:
    #                 if contract.working_hours:
    #                     scheduled_hours = \
    #                         contract.working_hours.get_hours_by_weekday(
    #                             dtDateTime.weekday())
    #
    #             # Actual number of hours worked on the day. Based on attendance
    #             # records.
    #             working_hours_on_day = self.attendance_dict_hours_on_day(
    #                 dtDateTime.date(), working_hours_dict)
    #
    #             # Is today a holiday?
    #             public_holiday = self.holidays_list_contains(
    #                 dtDateTime.date(), public_holidays_list)
    #
    #             # Keep count of the number of hours worked during the week for
    #             # weekly OT
    #             if dtDateTime.weekday() == contract.pps_id.ot_week_startday:
    #                 worked_hours_in_week = working_hours_on_day
    #             else:
    #                 worked_hours_in_week += working_hours_on_day
    #
    #             push_lsd = True
    #             if working_hours_on_day:
    #                 done = False
    #
    #                 if public_holiday:
    #                     _hours, push_lsd = self._book_holiday_hours(
    #                         contract, attendances,
    #                         holiday_obj, dtDateTime, rest_days, lsd,
    #                         working_hours_on_day)
    #                     if _hours == 0:
    #                         done = True
    #                     else:
    #                         working_hours_on_day = _hours
    #
    #                 # if not done and restday2_ot:
    #                 #     _hours, push_lsd = self._book_restday_hours(
    #                 #         contract, presence_policy, ot_policy,
    #                 #         attendances, dtDateTime, rest_days, lsd,
    #                 #         working_hours_on_day)
    #                 #     if _hours == 0:
    #                 #         done = True
    #                 #     else:
    #                 #         working_hours_on_day = _hours
    #
    #                 # if not done and restday_ot:
    #                 #     _hours, push_lsd = self._book_weekly_restday_hours(
    #                 #         contract, presence_policy, ot_policy,
    #                 #         attendances, dtDateTime, rest_days, lsd,
    #                 #         working_hours_on_day)
    #                 #     if _hours == 0:
    #                 #         done = True
    #                 #     else:
    #                 #         working_hours_on_day = _hours
    #
    #                 # if not done and weekly_ot:
    #                 #     # raise osv.except_osv(_('Attendance Error!'),
    #                 #     #                      _('There is not a final '
    #                 #     #                        'sign-out record for %s on')
    #                 #     #                      % (ot_policy.line_ids))
    #                 #     for line in ot_policy.line_ids:
    #                 #         if line.type == 'weekly' and (
    #                 #             not line.weekly_working_days or
    #                 #                         line.weekly_working_days == 0):
    #                 #             _active_after = float(line.active_after) / 60.0
    #                 #             if worked_hours_in_week > _active_after:
    #                 #                 if worked_hours_in_week - _active_after \
    #                 #                         > working_hours_on_day:
    #                 #                     attendances[line.code][
    #                 #                         'number_of_hours'] += \
    #                 #                         working_hours_on_day
    #                 #                 else:
    #                 #                     attendances[line.code][
    #                 #                         'number_of_hours'] += \
    #                 #                         worked_hours_in_week - \
    #                 #                         _active_after
    #                 #                 attendances[line.code][
    #                 #                     'number_of_days'] += 1.0
    #                 #                 done = True
    #                 #
    #                 # if not done and daily_ot:
    #                 #
    #                 #     # Do the OT between specified times (partial OT)
    #                 #     # first, so that it
    #                 #     # doesn't get double-counted in the regular OT.
    #                 #     partial_hr = 0
    #                 #     hours_after_ot = working_hours_on_day
    #                 #     for line in ot_policy.line_ids:
    #                 #         active_after_hrs = float(line.active_after) / 60.0
    #                 #         if line.type == 'daily' and working_hours_on_day \
    #                 #                 > active_after_hrs and \
    #                 #                 line.active_start_time:
    #                 #             partial_hr = att_obj.partial_hours_on_day(
    #                 #                 contract, dtDateTime, active_after_hrs,
    #                 #                 line.active_start_time,
    #                 #                 line.active_end_time, line.tz,
    #                 #                 punches_list=self.attendance_dict_list(
    #                 #                     working_hours_dict))
    #                 #             if partial_hr > 0:
    #                 #                 attendances[line.code][
    #                 #                     'number_of_hours'] += partial_hr
    #                 #                 attendances[line.code][
    #                 #                     'number_of_days'] += 1.0
    #                 #                 hours_after_ot -= partial_hr
    #                 #
    #                 #     for line in ot_policy.line_ids:
    #                 #         active_after_hrs = float(line.active_after) / 60.0
    #                 #         if line.type == 'daily' and hours_after_ot > \
    #                 #                 active_after_hrs and not \
    #                 #                 line.active_start_time:
    #                 #             attendances[line.code][
    #                 #                 'number_of_hours'] += hours_after_ot - (
    #                 #                 float(line.active_after) / 60.0)
    #                 #             attendances[line.code]['number_of_days'] += 1.0
    #
    #                 # if not done:
    #                 #     raise osv.except_osv(_('Attendance Error!'),
    #                 #                 _('There is not a final sign-out record '
    #                 #                   'for %s on') % (hasattr(
    #                 #                     presence_policy, 'line_ids')))
    #                 #     if hasattr(presence_policy, 'line_ids'):
    #                 #         for line in presence_policy.line_ids:
    #                 #             if line.type == 'normal':
    #                 #                 normal_hours = self._get_applied_time(
    #                 #                     working_hours_on_day,
    #                 #                     line.active_after,
    #                 #                     line.duration)
    #                 #                 attendances[line.code][
    #                 #                     'number_of_hours'] += normal_hours
    #                 #                 attendances[line.code]['number_of_days'] \
    #                 #                     += 1.0
    #                 #                 done = True
    #                 #                 _l.warning('nh: %s', normal_hours)
    #                 #                 _l.warning('att: %s', attendances[
    #                 #                     line.code])
    #
    #                 if push_lsd:
    #                     lsd.push(True)
    #             else:
    #                 lsd.push(False)
    #
    #             leave_type, leave_hours = self.leaves_list_get_hours(
    #                 contract.employee_id.id,
    #                 contract.id, contract.working_hours,
    #                 day_from + timedelta(days=day), leaves_list)
    #
    #             # Find leave type ID
    #             lt_data = False
    #             if leave_type:
    #                 lt_data = self.env['hr.holidays.status'].search(
    #                     [('code', '=', leave_type)])
    #             rest_days_ok = True
    #             public_holidays_ok = True
    #             if lt_data:
    #                 if lt_data.ex_rest_days:
    #                     if dtDateTime.weekday() in rest_days:
    #                         rest_days_ok = False
    #                 if lt_data.ex_public_holidays:
    #                     if lt_data.ex_public_holidays and public_holiday:
    #                         public_holidays_ok = False
    #
    #             if leave_type and rest_days_ok and public_holidays_ok:
    #                 if isinstance(leave_hours, list):
    #                     leave_hours = leave_hours[0]
    #                 if leave_type in leaves:
    #                     leaves[leave_type]['number_of_days'] += 1.0
    #                     leaves[leave_type]['number_of_hours'] += \
    #                         (leave_hours > scheduled_hours) and \
    #                         scheduled_hours or leave_hours
    #                 else:
    #                     leaves[leave_type] = {
    #                         'name': leave_type,
    #                         'sequence': 8,
    #                         'code': leave_type,
    #                         'number_of_days': 1.0,
    #                         'number_of_hours':
    #                             (leave_hours > scheduled_hours) and
    #                             scheduled_hours or leave_hours,
    #                         'contract_id': contract.id,
    #                     }
    #             elif awol_code and \
    #                     (scheduled_hours > 0 and
    #                      working_hours_on_day < scheduled_hours) \
    #                     and not public_holiday:
    #                 hours_diff = scheduled_hours - working_hours_on_day
    #                 leaves[awol_code]['number_of_days'] += 1.0
    #                 leaves[awol_code]['number_of_hours'] += hours_diff
    #
    #             # Calculate total possible working hours in the month
    #             if dtDateTime.weekday() not in rest_days:
    #                 attendances['MAX'][
    #                     'number_of_hours'] += normal_working_hours
    #                 attendances['MAX']['number_of_days'] += 1
    #
    #         leaves = [value for key, value in leaves.items()]
    #
    #         # ###Tamkeen###
    #         month_last_day = calendar.monthrange(day_to.year, day_to.month)[1]
    #         for leave_input in leaves:
    #             if leave_input['number_of_days']:
    #                 actual_leave_days = leave_input['number_of_days']
    #                 if month_last_day == 29 and day_to.month == 2 and \
    #                         leave_type:
    #                     actual_leave_days += 1
    #                 elif month_last_day == 28 and day_to.month == 2 and \
    #                         leave_type:
    #                     actual_leave_days += 2
    #                 elif month_last_day == 31 and actual_leave_days >= 2 and \
    #                         leave_type:
    #                     actual_leave_days -= 1
    #                 elif month_last_day == 31 and actual_leave_days == 1 and \
    #                         leave_type:
    #                     actual_leave_days = 0
    #                 leave_input.update({"number_of_days": actual_leave_days})
    #         # #############
    #         attendances = [value for key, value in attendances.items()]
    #         res += attendances + leaves
    #     return res

    # @api.model
    # def _partial_period_factor(self, payslip, contract):
    #     """
    #     :param payslip: Payslip record
    #     :param contract: Contract record
    #     :return:
    #     """
    #     dpsFrom = datetime.strptime(payslip.date_from, OE_DATEFORMAT).date()
    #     dpsTo = datetime.strptime(payslip.date_to, OE_DATEFORMAT).date()
    #     dcStart = datetime.strptime(contract.date_start, OE_DATEFORMAT).date()
    #     dcEnd = False
    #     if (contract.date_end):
    #         dcEnd = datetime.strptime(contract.date_end, OE_DATEFORMAT).date()
    #
    #     # both start and end of contract are out of the bounds of the payslip
    #     if dcStart <= dpsFrom and (not dcEnd or dcEnd >= dpsTo):
    #         return 1
    #
    #     # One or both start and end of contract are within the bounds of the
    #     #  payslip
    #     nocontract_days = 0
    #     if dcStart > dpsFrom:
    #         nocontract_days += (dcStart - dpsFrom).days
    #     if dcEnd and dcEnd < dpsTo:
    #         nocontract_days += (dpsTo - dcEnd).days
    #     total_days = (dpsTo - dpsFrom).days + 1
    #     contract_days = total_days - nocontract_days
    #     return (float(contract_days) / float(total_days))

    # @api.model
    # def get_utilities_dict(self, contract, payslip):
    #     res = {}
    #     if not contract or not payslip:
    #         return res
    #
    #     # Calculate percentage of pay period in which contract lies
    #     res.update(
    #         {'PPF': {'amount': self._partial_period_factor(payslip,
    #                                                        contract)}})
    #
    #     # Calculate net amount of previous payslip
    #     imd_obj = self.env['ir.model.data']
    #     hr_payslip_obj = self.env['hr.payslip']
    #     ps_ids = hr_payslip_obj.search([
    #         ('employee_id', '=', contract.employee_id.id)],
    #         order='date_from').ids
    #     res.update({'PREVPS':
    #                 {'exists': 0,
    #                  'net': 0}
    #                 })
    #     if len(ps_ids) > 0:
    #         # Get database ID of Net salary category
    #         res_model, net_id = imd_obj.get_object_reference(
    #             'hr_payroll', 'NET')
    #
    #         ps = hr_payslip_obj.browse(ps_ids[-1])
    #         res['PREVPS']['exists'] = 1
    #         total = 0
    #         for line in ps.line_ids:
    #             if line.salary_rule_id.category_id.id == net_id:
    #                 total += line.total
    #         res['PREVPS']['net'] = total
    #
    #     return res

    # XXX
    # Copied (almost) verbatim from hr_payroll for the sole purpose of
    # adding the 'utils'
    # object to localdict.
    # @api.model
    # def get_payslip_lines(self, contract_ids, payslip_id):
    #     def _sum_salary_rule_category(localdict, category, amount):
    #         if category.parent_id:
    #             localdict = _sum_salary_rule_category(localdict,
    #                                                   category.parent_id,
    #                                                   amount)
    #         localdict[
    #             'categories'].dict[category.code] = \
    #             category.code in localdict['categories'].dict and \
    #             localdict['categories'].dict[category.code] + amount or amount
    #         return localdict
    #
    #     class BrowsableObject(object):
    #
    #         def __init__(self, employee_id, dict, env):
    #             self.employee_id = employee_id
    #             self.dict = dict
    #             self.env = env
    #
    #         def __getattr__(self, attr):
    #             return attr in self.dict and self.dict.__getitem__(attr) or 0.0
    #
    #     class InputLine(BrowsableObject):
    #         """a class that will be used into the python code, mainly for
    #         usability purposes"""
    #
    #         def sum(self, code, from_date, to_date=None):
    #             if to_date is None:
    #                 to_date = fields.Date.today()
    #             self.env.cr.execute("""
    #                 SELECT sum(amount) as sum
    #                 FROM hr_payslip as hp, hr_payslip_input as pi
    #                 WHERE hp.employee_id = %s AND hp.state = 'done'
    #                 AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id =
    #                 pi.payslip_id AND pi.code = %s""",
    #                                 (self.employee_id, from_date, to_date,
    #                                  code))
    #             return self.env.cr.fetchone()[0] or 0.0
    #
    #     class WorkedDays(BrowsableObject):
    #         """a class that will be used into the python code, mainly for
    #         usability purposes"""
    #
    #         def _sum(self, code, from_date, to_date=None):
    #             if to_date is None:
    #                 to_date = fields.Date.today()
    #             self.env.cr.execute("""
    #                 SELECT sum(number_of_days) as number_of_days,
    #                 sum(number_of_hours) as number_of_hours
    #                 FROM hr_payslip as hp, hr_payslip_worked_days as pi
    #                 WHERE hp.employee_id = %s AND hp.state = 'done'
    #                 AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id =
    #                 pi.payslip_id AND pi.code = %s""",
    #                                 (self.employee_id, from_date, to_date,
    #                                  code))
    #             return self.env.cr.fetchone()
    #
    #         def sum(self, code, from_date, to_date=None):
    #             res = self._sum(code, from_date, to_date)
    #             return res and res[0] or 0.0
    #
    #         def sum_hours(self, code, from_date, to_date=None):
    #             res = self._sum(code, from_date, to_date)
    #             return res and res[1] or 0.0
    #
    #     class Payslips(BrowsableObject):
    #         """a class that will be used into the python code, mainly for
    #         usability purposes"""
    #
    #         def sum(self, code, from_date, to_date=None):
    #             if to_date is None:
    #                 to_date = fields.Date.today()
    #             self.env.cr.execute("""SELECT sum(case when hp.credit_note
    #              = False then (pl.total) else (-pl.total) end)
    #                         FROM hr_payslip as hp, hr_payslip_line as pl
    #                         WHERE hp.employee_id = %s AND hp.state = 'done'
    #                         AND hp.date_from >= %s AND hp.date_to <= %s AND
    #                         hp.id = pl.slip_id AND pl.code = %s""",
    #                                 (self.employee_id, from_date, to_date,
    #                                  code))
    #             res = self.env.cr.fetchone()
    #             return res and res[0] or 0.0
    #
    #             # we keep a dict with the result because a value can be
    #             # overwritten by another rule with the same code
    #             # rules replace with rules_dict
    #             # categories_dict not in v10
    #
    #     result_dict = {}
    #     rules_dict = {}
    #     worked_days_dict = {}
    #     inputs_dict = {}
    #     blacklist = []
    #
    #     payslip = self.env['hr.payslip'].browse(payslip_id)
    #     for worked_days_line in payslip.worked_days_line_ids:
    #         worked_days_dict[worked_days_line.code] = worked_days_line
    #     for input_line in payslip.input_line_ids:
    #         inputs_dict[input_line.code] = input_line
    #
    #     categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
    #     inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
    #     worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict,
    #                              self.env)
    #     payslips = Payslips(payslip.employee_id.id, payslip, self.env)
    #     rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
    #
    #     baselocaldict = {'categories': categories, 'rules': rules,
    #                      'payslip': payslips, 'worked_days': worked_days,
    #                      'inputs': inputs}
    #     # get the ids of the structures on the contracts and their parent id
    #     #  as well
    #     contracts = self.env['hr.contract'].browse(contract_ids)
    #     structure_ids = contracts.get_all_structures()
    #     # get the rules of the structure and thier children
    #     rule_ids = self.env['hr.payroll.structure'].browse(
    #         structure_ids).get_all_rules()
    #     sorted_rule_ids = [id for id, sequence in sorted(rule_ids,
    #                                                      key=lambda x: x[1])]
    #     sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)
    #     for contract in contracts:
    #         employee = contract.employee_id
    #         localdict = dict(baselocaldict, employee=employee,
    #                          contract=contract)
    #         temp_dict = {}
    #         utils_dict = self.get_utilities_dict(contract, payslip)
    #         for key, value in utils_dict.iteritems():
    #             k_obj = BrowsableObject(payslip.employee_id.id, value,
    #                                     self.env)
    #             temp_dict.update({key: k_obj})
    #         utils_obj = BrowsableObject(payslip.employee_id.id, temp_dict,
    #                                     self.env)
    #         localdict.update({'utils': utils_obj})
    #         for rule in sorted_rules:
    #             number_of_days_new_employee = self.number_of_days_new_employee
    #             key = rule.code + '-' + str(contract.id)
    #             localdict['result'] = None
    #             localdict['result_qty'] = 1.0
    #             localdict['result_rate'] = 100
    #             # check if the rule can be applied
    #             if rule.satisfy_condition(localdict) and rule.id not in \
    #                     blacklist:
    #                 # compute the amount of the rule
    #                 amount, qty, rate = rule.compute_rule(localdict)
    #                 amount = (amount * number_of_days_new_employee) / 30
    #                 # check if there is already a rule computed with that code
    #                 previous_amount = rule.code in localdict and localdict[
    #                     rule.code] or 0.0
    #                 # set/overwrite the amount computed for this rule in the
    #                 # localdict
    #                 tot_rule = amount * qty * rate / 100.0
    #                 localdict[rule.code] = tot_rule
    #                 rules_dict[rule.code] = rule
    #                 # sum the amount for its salary category
    #                 localdict = _sum_salary_rule_category(localdict,
    #                                                       rule.category_id,
    #                                                       tot_rule -
    #                                                       previous_amount)
    #                 # create/overwrite the rule in the temporary results
    #                 result_dict[key] = {
    #                     'salary_rule_id': rule.id,
    #                     'contract_id': contract.id,
    #                     'name': rule.name,
    #                     'code': rule.code,
    #                     'category_id': rule.category_id.id,
    #                     'sequence': rule.sequence,
    #                     'appears_on_payslip': rule.appears_on_payslip,
    #                     'condition_select': rule.condition_select,
    #                     'condition_python': rule.condition_python,
    #                     'condition_range': rule.condition_range,
    #                     'condition_range_min': rule.condition_range_min,
    #                     'condition_range_max': rule.condition_range_max,
    #                     'amount_select': rule.amount_select,
    #                     'amount_fix': rule.amount_fix,
    #                     'amount_python_compute': rule.amount_python_compute,
    #                     'amount_percentage': rule.amount_percentage,
    #                     'amount_percentage_base': rule.amount_percentage_base,
    #                     'register_id': rule.register_id.id,
    #                     'amount': amount,
    #                     'employee_id': contract.employee_id.id,
    #                     'quantity': qty,
    #                     'rate': rate,
    #                 }
    #             else:
    #                 # blacklist this rule and its children
    #                 blacklist += [id for id, seq in
    #                               rule._recursive_search_of_rules()]
    #     return [value for code, value in result_dict.items()]


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _inherit = 'hr.payslip.line'

    amount = fields.Float('Amount',
                          digits=dp.get_precision('Intermediate Payroll'))


class HrAttendance(models.Model):
    _name = 'hr.attendance'
    _inherit = 'hr.attendance'

    @api.model
    def _calculate_rollover(self, utcdt, rollover_hours):
        # XXX - assume time part of utcdt is already set to midnight
        return utcdt + timedelta(hours=int(rollover_hours))

    @api.model
    def punches_list_init(self, employee_id, pps_template, dFrom, dTo):
        """
        Returns a dict containing a key for each day in range dFrom -
        dToday and a corresponding tuple containing two list: in punches,
        and the corresponding out punches.
        - Convert datetime to tz aware datetime according to tz in pay
        period schedule, then to UTC, and
        - then to naive datetime for comparison with values in db.
        - includue records 48 hours previous to and 48 hours after the desired
        - dates so that any requests for rollover, sessions, etc are can be
        satisfied
        :param employee_id: Employee Id
        :param pps_template:
        :param dFrom: Date From
        :param dTo: Date to
        :return:
        """
        res = []
        # Comment for Release 1
        # dtFrom = datetime.strptime(dFrom.strftime(
        #     OE_DATEFORMAT) + ' 00:00:00', OE_DATETIMEFORMAT)
        # dtFrom += timedelta(hours=-48)
        # dtTo = datetime.strptime(dTo.strftime(
        #     OE_DATEFORMAT) + ' 00:00:00', OE_DATETIMEFORMAT)
        # dtTo += timedelta(hours=+48)
        # utcdtFrom = timezone(pps_template.tz).localize(
        #     dtFrom, is_dst=False).astimezone(utc)
        # utcdtTo = timezone(pps_template.tz).localize(
        #     dtTo, is_dst=False).astimezone(utc)
        # utcdtDay = utcdtFrom
        # utcdtDayEnd = utcdtTo + timedelta(days=+1, seconds=-1)
        # ndtDay = utcdtDay.replace(tzinfo=None)
        # ndtDayEnd = utcdtDayEnd.replace(tzinfo=None)
        #
        # ids = self.search([
        #     ('employee_id', '=', employee_id), '&',
        #     ('check_in', '>=', ndtDay.strftime(OE_DATETIMEFORMAT)),
        #     ('check_out', '<=', ndtDayEnd.strftime(OE_DATETIMEFORMAT))])
        # for a in ids:
        #     res.append((a.action, a.name))
        return res

    # @api.model
    # def punches_list_search(self, ndtFrom, ndtTo, punches_list):
    #     """
    #     Get and Return Purchase List
    #     :param ndtFrom: From Date
    #     :param ndtTo: To date
    #     :param punches_list:
    #     :return:
    #     """
    #     res = []
    #     for action, name in punches_list:
    #         ndtName = datetime.strptime(name, OE_DATETIMEFORMAT)
    #         if ndtName >= ndtFrom and ndtName <= ndtTo:
    #             res.append((action, name))
    #     return res

    # @api.model
    # def _get_normalized_punches(self, employee_id, pps_template, dDay,
    #                             punches_list):
    #     """
    #     Returns a tuple containing two lists: in punches, and corresponding
    #     out punches
    #     - We assume that:
    #       * No dangling sign-in or sign-out
    #     :param employee_id: Employee Id
    #     :param pps_template:
    #     :param dDay: Days
    #     :param punches_list: List
    #     :return:
    #     """
    #     # Convert datetime to tz aware datetime according to tz in pay
    #     # period schedule, then to UTC, and then to naive datetime for
    #     # comparison with values in db.
    #     dt = datetime.strptime(
    #         dDay.strftime(OE_DATEFORMAT) + ' 00:00:00', OE_DATETIMEFORMAT)
    #     utcdtDay = timezone(pps_template.tz).localize(
    #         dt, is_dst=False).astimezone(utc)
    #     utcdtDayEnd = utcdtDay + timedelta(days=+1, seconds=-1)
    #     ndtDay = utcdtDay.replace(tzinfo=None)
    #     ndtDayEnd = utcdtDayEnd.replace(tzinfo=None)
    #     my_list = self.punches_list_search(ndtDay, ndtDayEnd, punches_list)
    #     if len(my_list) == 0:
    #         return [], []
    #     # We are assuming attendances are normalized: (in, out, in, out, ...)
    #
    #     sin = []
    #     sout = []
    #     for action, name in my_list:
    #         if action == 'sign_in':
    #             sin.append(name)
    #         elif action == 'sign_out':
    #             sout.append(name)
    #     if len(sin) == 0 and len(sout) == 0:
    #         return [], []
    #     # CHECKS AT THE START OF THE DAY
    #     # Remove sessions that would have been included in yesterday's
    #     # @attendance.
    #     # We may have a a session *FROM YESTERDAY* that crossed-over into
    #     # today. If it is greater than the maximum continuous hours allowed
    #     # into the next day (as configured in the pay period schedule),
    #     # then count only the difference between the actual and the maximum
    #     # continuous hours.
    #
    #     dtRollover = (self._calculate_rollover(
    #         utcdtDay, pps_template.ot_max_rollover_hours)).replace(tzinfo=None)
    #     if (len(sout) - len(sin)) == 0:
    #         if len(sout) > 0:
    #             dtSout = datetime.strptime(sout[0], OE_DATETIMEFORMAT)
    #             dtSin = datetime.strptime(sin[0], OE_DATETIMEFORMAT)
    #             if dtSout > dtRollover and (dtSout < dtSin):
    #                 sin = [dtRollover.strftime(OE_DATETIMEFORMAT)] + sin
    #             elif dtSout < dtSin:
    #                 sout = sout[1:]
    #                 # There may be another session that starts within the
    #                 # rollover period
    #                 if dtSin < dtRollover and float((dtSin - dtSout).seconds) \
    #                         / 60.0 >= pps_template.ot_max_rollover_gap:
    #                     sin = sin[1:]
    #                     sout = sout[1:]
    #         else:
    #             return [], []
    #     elif (len(sout) - len(sin)) == 1:
    #         dtSout = datetime.strptime(sout[0], OE_DATETIMEFORMAT)
    #         if dtSout > dtRollover:
    #             sin = [dtRollover.strftime(OE_DATETIMEFORMAT)] + sin
    #         else:
    #             sout = sout[1:]
    #             # There may be another session that starts within the rollover
    #             # period
    #             dtSin = False
    #             if len(sin) > 0:
    #                 dtSin = datetime.strptime(sin[0], OE_DATETIMEFORMAT)
    #             if dtSin and dtSin < dtRollover and float(
    #                     (dtSin - dtSout).seconds) / 60.0 >= \
    #                     pps_template.ot_max_rollover_gap:
    #                 sin = sin[1:]
    #                 sout = sout[1:]
    #     # If the first sign-in was within the rollover gap *AT* midnight
    #     # check to, see if there are any sessions within the rollover gap
    #     # before it.
    #
    #     if len(sout) > 0:
    #         ndtSin = datetime.strptime(sin[0], OE_DATETIMEFORMAT)
    #         if (ndtSin - timedelta(
    #                 minutes=pps_template.ot_max_rollover_gap)) <= ndtDay:
    #             my_list4 = self.punches_list_search(ndtDay + timedelta(
    #                 hours=-24),
    #                 ndtDay + timedelta(
    #                 seconds=-1),
    #                 punches_list)
    #             if len(my_list4) > 0:
    #                 if (my_list4[-1].action == 'sign_out'):
    #                     ndtSout = datetime.strptime(
    #                         my_list4[-1].name, OE_DATETIMEFORMAT)
    #                     if (ndtSin <= ndtSout + timedelta(
    #                             minutes=pps_template.ot_max_rollover_gap)):
    #                         sin = sin[1:]
    #                         sout = sout[1:]
    #     # CHECKS AT THE END OF THE DAY
    #     # Include sessions from tomorrow that should be included in today's
    #     # attendance.
    #     # We may have a session that crosses the midnight boundary. If so,
    #     # add it to today's session.
    #
    #     dtRollover = (self._calculate_rollover(
    #         ndtDay + timedelta(days=1),
    #         pps_template.ot_max_rollover_hours)).replace(tzinfo=None)
    #     if (len(sin) - len(sout)) == 1:
    #
    #         my_list2 = self.punches_list_search(
    #             ndtDayEnd + timedelta(seconds=+1),
    #             ndtDayEnd + timedelta(days=1), punches_list)
    #         emp_name = self.env['hr.employee'].browse(employee_id).name
    #         if len(my_list2) == 0:
    #             raise Warning(_('Attendance Error!'
    #                             'There is not a final sign-out record '
    #                             'for %s on %s') % (emp_name, dDay))
    #         action, name = my_list2[0]
    #         if action == 'sign_out':
    #             dtSout = datetime.strptime(name, OE_DATETIMEFORMAT)
    #             if dtSout > dtRollover:
    #                 sout.append(dtRollover.strftime(OE_DATETIMEFORMAT))
    #             else:
    #                 sout.append(name)
    #                 # There may be another session within the OT max. rollover
    #                 # gap
    #                 if len(my_list2) > 2 and my_list2[1][0] == 'sign_in':
    #                     dtSin = datetime.strptime(name, OE_DATETIMEFORMAT)
    #                     if float((dtSin - dtSout).seconds) / 60.0 < \
    #                             pps_template.ot_max_rollover_gap:
    #                         sin.append(my_list2[1][1])
    #                         sout.append(my_list2[2][1])
    #         else:
    #             raise Warning(_('Attendance Error!'
    #                             'There is a sign-in with no corresponding '
    #                             'sign-out for %s on %s') % (emp_name, dDay))
    #     # If the last sign-out was within the rollover gap *BEFORE* midnight
    #     #  check to, see if there are any sessions within the rollover gap
    #     # after it.
    #
    #     if len(sout) > 0:
    #         ndtSout = datetime.strptime(sout[-1], OE_DATETIMEFORMAT)
    #         if (ndtDayEnd - timedelta(
    #                 minutes=pps_template.ot_max_rollover_gap)) <= ndtSout:
    #             my_list3 = self.punches_list_search(ndtDayEnd + timedelta(
    #                 seconds=+1),
    #                 ndtDayEnd + timedelta(
    #                 hours=+24),
    #                 punches_list)
    #             if len(my_list3) > 0:
    #                 action, name = my_list3[0]
    #                 ndtSin = datetime.strptime(name, OE_DATETIMEFORMAT)
    #                 if (ndtSin <= ndtSout + timedelta(
    #                     minutes=pps_template.ot_max_rollover_gap)) and \
    #                         action == 'sign_in':
    #                     sin.append(name)
    #                     sout.append(my_list3[1][1])
    #     return sin, sout

    # @api.model
    # def _on_day(self, contract, dDay, punches_list=None):
    #     """
    #     Return two lists: the first is sign-in times, and the second is
    #     corresponding sign-outs.
    #     :param contract: Contract Record
    #     :param dDay: Days
    #     :param punches_list: List
    #     :return:
    #     """
    #     if punches_list is None:
    #         punches_list = self.punches_list_init(
    #             contract.employee_id.id, contract.pps_id,
    #             dDay, dDay)
    #
    #     sin, sout = self._get_normalized_punches(
    #         contract.employee_id.id, contract.pps_id,
    #         dDay, punches_list)
    #     if len(sin) != len(sout):
    #         raise Warning(_(
    #             'Number of Sign-in and Sign-out records do not match!'
    #             'Employee: %s\nSign-in(s): %s\nSign-out(s): %s') % (
    #             contract.employee_id.name, sin, sout))
    #     return sin, sout

    # @api.model
    # def punch_names_on_day(self, contract, dDay, punches_list=None):
    #     """
    #     Return a list of tuples containing in and corresponding out punches
    #     for the day.
    #     :param contract: Contract Record
    #     :param dDay: Days
    #     :param punches_list: List
    #     :return:
    #     """
    #     sin, sout = self._on_day(contract, dDay, punches_list=punches_list)
    #     res = []
    #     for i in range(0, len(sin)):
    #         res.append((sin[i], sout[i]))
    #     return res

    # @api.model
    # def punch_ids_on_day(self, contract, dDay, punches_list=None):
    #     """
    #     Return a list of database ids of punches for the day.
    #     :param contract: Contract Record
    #     :param dDay: Days
    #     :param punches_list: List
    #     :return:
    #     """
    #     sin, sout = self._on_day(contract, dDay, punches_list=punches_list)
    #     names = []
    #     for i in range(0, len(sin)):
    #         names.append(sin[i])
    #         names.append(sout[i])
    #     return self.search([
    #         ('employee_id', '=', contract.employee_id.id),
    #         ('name', 'in', names)],
    #         order='name').ids

    # @api.model
    # def total_hours_on_day(self, contract, dDay, punches_list=None):
    #     """
    #     Calculate the number of hours worked on specified date.
    #     :param contract: Contract Record
    #     :param dDay: Days
    #     :param punches_list: List
    #     :return:
    #     """
    #     sin, sout = self._on_day(contract, dDay,
    #                              punches_list=punches_list)
    #     worked_hours = 0
    #     for i in range(0, len(sin)):
    #         start = datetime.strptime(sin[i], OE_DATETIMEFORMAT)
    #         end = datetime.strptime(sout[i], OE_DATETIMEFORMAT)
    #         worked_hours += float((end - start).seconds) / 60.0 / 60.0
    #     return worked_hours

    # @api.model
    # def partial_hours_on_day(self, contract, dtDay, active_after, begin,
    #                          stop, tz, punches_list=None):
    #     """
    #     Calculate the number of hours worked between begin and stop hours, but
    #     after active_after hours past the beginning of the first sign-in on
    #     specified date.
    #     :param contract: Contracr Record
    #     :param dtDay: Days
    #     :param active_after:
    #     :param begin:
    #     :param stop:
    #     :param tz:
    #     :param punches_list: List
    #     :return:
    #     """
    #     # Since OpenERP stores datetime in db as UTC, but in naive format we
    #     #  have to do, the following to compare our partial time to the time
    #     # in db:
    #     # 1. Make our partial time into a naive datetime
    #     # 2. Localize the naive datetime to the timezone specified by our
    #     #    caller
    #     # 3. Convert our localized datetime to UTC
    #     # 4. Convert our UTC datetime back into naive datetime format
    #
    #     dtBegin = datetime.strptime(
    #         dtDay.strftime(OE_DATEFORMAT) + ' ' + begin + ':00',
    #         OE_DATETIMEFORMAT)
    #     dtStop = datetime.strptime(
    #         dtDay.strftime(OE_DATEFORMAT) + ' ' + stop + ':00',
    #         OE_DATETIMEFORMAT)
    #     if dtStop <= dtBegin:
    #         dtStop += timedelta(days=1)
    #     utcdtBegin = timezone(tz).localize(
    #         dtBegin, is_dst=False).astimezone(utc)
    #     utcdtStop = timezone(tz).localize(dtStop, is_dst=False).astimezone(utc)
    #     dtBegin = utcdtBegin.replace(tzinfo=None)
    #     dtStop = utcdtStop.replace(tzinfo=None)
    #
    #     if punches_list is None:
    #         punches_list = self.punches_list_init(
    #             contract.employee_id.id, contract.pps_id,
    #             dtDay.date(), dtDay.date())
    #     sin, sout = self._get_normalized_punches(
    #         contract.employee_id.id, contract.pps_id,
    #         dtDay.date(), punches_list)
    #     worked_hours = 0
    #     lead_hours = 0
    #     for i in range(0, len(sin)):
    #         start = datetime.strptime(sin[i], OE_DATETIMEFORMAT)
    #         end = datetime.strptime(sout[i], OE_DATETIMEFORMAT)
    #         if worked_hours == 0 and end <= dtBegin:
    #             lead_hours += float((end - start).seconds) / 60.0 / 60.0
    #         elif worked_hours == 0 and end > dtBegin:
    #             if start < dtBegin:
    #                 lead_hours += float(
    #                     (dtBegin - start).seconds) / 60.0 / 60.0
    #                 start = dtBegin
    #             if end > dtStop:
    #                 end = dtStop
    #             worked_hours = float((end - start).seconds) / 60.0 / 60.0
    #         elif worked_hours > 0 and start < dtStop:
    #             if end > dtStop:
    #                 end = dtStop
    #             worked_hours += float((end - start).seconds) / 60.0 / 60.0
    #
    #     if worked_hours == 0:
    #         return 0
    #     elif lead_hours >= active_after:
    #         return worked_hours
    #
    #     return max(0, (worked_hours + lead_hours) - active_after)


class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    @api.multi
    def _get_wage_hourly(self):
        """
        Hourly wage calculation
        :return:
        """
        for contract_rec in self:
            rate = 0.0
            if contract_rec.wage_type == 'hourly':
                rate = contract_rec.wage
            elif contract_rec.wage_type == 'daily':
                rate = contract_rec.wage / 8.0
            elif contract_rec.wage_type == 'salary':
                rate = contract_rec.wage / 26.0 / 8.0
            contract_rec.wage_hourly = rate

    @api.multi
    def _get_wage_daily(self):
        """
        Daily Wage Calculation.
        :return:
        """
        for contract_rec in self:
            rate = 0.0
            if contract_rec.wage_type == 'hourly':
                rate = contract_rec.wage * 8.0
            elif contract_rec.wage_type == 'daily':
                rate = contract_rec.wage
            elif contract_rec.wage_type == 'salary':
                rate = contract_rec.wage / 26.0
            contract_rec.wage_daily = rate

    @api.multi
    def _get_wage_monthly(self):
        """
        Monthly Wage Calculation
        :return:
        """
        for contract_rec in self:
            rate = 0.0
            if contract_rec.wage_type == 'hourly':
                rate = contract_rec.wage * 8.0 * 26.0
            elif contract_rec.wage_type == 'daily':
                rate = contract_rec.wage * 26
            elif contract_rec.wage_type == 'salary':
                rate = contract_rec.wage
            contract_rec.wage_monthly = rate

    wage_type = fields.Selection([('hourly', 'Hourly'),
                                  ('daily', 'Daily'),
                                  ('salary', 'Salary')],
                                 string='Wage Type',
                                 # required=True
                                 default='salary')
    wage_hourly = fields.Float(compute=_get_wage_hourly,
                               digits=dp.get_precision(
                                   'Intermediate Payroll'),
                               string='Hourly Wages')
    wage_daily = fields.Float(compute=_get_wage_daily,
                              digits=dp.get_precision(
                                  'Intermediate Payroll'),
                              string='Daily Wages')
    wage_monthly = fields.Float(compute=_get_wage_monthly,
                                digits=dp.get_precision(
                                    'Intermediate Payroll'),
                                string='Monthly Wages')


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _inherit = 'hr.payslip.worked_days'

    rate = fields.Float('Rate', default=0.0)  # required=True
