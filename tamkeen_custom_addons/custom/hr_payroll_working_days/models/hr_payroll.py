# from openerp.exceptions import Warning
# from dateutil.relativedelta import relativedelta
# from pytz import timezone, utc
# import openerp.addons.decimal_precision as dp
# from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.addons.hr_payroll_extension.models.hr_payroll import last_X_days
import calendar
from odoo import api, models


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that
        should be applied for the given contract between date_from and date_to
        """
        sched_obj = self.env['hr.schedule']
        sched_detail_obj = self.env['hr.schedule.detail']
        holiday_obj = self.env['hr.holidays.public']

        day_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        day_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        nb_of_days = (day_to - day_from).days + 1
        # ###Tamkeen####
        actual_leave_days = 0
        # ##############
        # Initialize list of public holidays. We only need to calculate
        # it once during the lifetime of this object so attach it directly
        # to it.
        try:
            public_holidays_list = self._mtm_public_holidays_list
        except AttributeError:
            self._mtm_public_holidays_list = self.holidays_list_init(
                day_from, day_to)
            public_holidays_list = self._mtm_public_holidays_list

        def get_ot_policies(policy_group_id, day, data):
            if data is None or not data['_reuse']:
                data = {
                    'policy': None,
                    'daily': None,
                    'restday2': None,
                    'restday': None,
                    'weekly': None,
                    'holiday': None,
                    '_reuse': False,
                }
            elif data['_reuse']:
                return data

            ot_policy = self._get_ot_policy(policy_group_id, day)
            daily_ot = ot_policy and len(ot_policy.daily_codes()) > 0 or None
            restday2_ot = ot_policy and len(ot_policy.restday2_codes()) > 0 \
                or None
            restday_ot = ot_policy and len(ot_policy.restday_codes()) > 0 \
                or None
            weekly_ot = ot_policy and len(ot_policy.weekly_codes()) > 0 or \
                None
            holiday_ot = ot_policy and len(ot_policy.holiday_codes()) > 0 \
                or None

            data['policy'] = ot_policy
            data['daily'] = daily_ot
            data['restday2'] = restday2_ot
            data['restday'] = restday_ot
            data['weekly'] = weekly_ot
            data['holiday'] = holiday_ot
            return data

        def get_absence_policies(policy_group_id, day, data):
            if data is None or not data['_reuse']:
                data = {
                    'policy': None,
                    '_reuse': False,
                }
            elif data['_reuse']:
                return data
            absence_policy = self._get_absence_policy(policy_group_id, day)
            data['policy'] = absence_policy
            return data

        def get_presence_policies(policy_group_id, day, data):
            if data is None or not data['_reuse']:
                data = {
                    'policy': None,
                    '_reuse': False,
                }
            elif data['_reuse']:
                return data
            policy = self._get_presence_policy(policy_group_id, day)
            data['policy'] = policy
            return data

        res = []
        for contract in self.env['hr.contract'].browse(contract_ids):
            worked_hours_in_week = 0
            # Initialize list of leave's taken by the employee during the month

            if not contract.pps_id:
                raise Warning(_('Warning !'
                                '\nPlease set Payroll Period Schedule for \n'
                                'Employee : %s \nContract : %s') % (
                    contract.employee_id.name, contract.name))
            leaves_list = self.leaves_list_init(contract.employee_id.id,
                                                day_from, day_to,
                                                contract.pps_id.tz)

            # Get default set of rest days for this employee/contract
            contract_rest_days = []
            if contract.working_hours:
                contract_rest_days = \
                    contract.working_hours.get_rest_days()
            # Initialize dictionary of dates in this payslip and the hours the
            # employee was scheduled to work on each
            sched_hours_dict = \
                sched_detail_obj.scheduled_begin_end_times_range(
                    contract.employee_id.id, contract.id, day_from, day_to)
            # Initialize dictionary of hours worked per day
            working_hours_dict = self.attendance_dict_init(
                contract, day_from, day_to)

            # Short-circuit:
            # If the policy for the first day is the same as the one for the
            # last day assume that it will also be the same for the days in
            # between, and reuse the same policy instead of checking for
            # every day.
            ot_data = None
            data2 = None

            ot_data = get_ot_policies(contract.policy_group_id, day_from,
                                      ot_data)
            data2 = get_ot_policies(contract.policy_group_id, day_to, data2)
            if (ot_data['policy'] and data2['policy']) and ot_data[
                    'policy'].id == data2['policy'].id:
                ot_data['_reuse'] = True

            absence_data = None
            data2 = None
            absence_data = get_absence_policies(
                contract.policy_group_id, day_from, absence_data)
            data2 = get_absence_policies(
                contract.policy_group_id, day_to, data2)
            if (absence_data['policy'] and data2['policy']) and \
                    absence_data['policy'].id == data2['policy'].id:
                absence_data['_reuse'] = True

            presence_data = None
            data2 = None
            presence_data = get_presence_policies(
                contract.policy_group_id, day_from, presence_data)
            data2 = get_presence_policies(
                contract.policy_group_id, day_to, data2)
            if (presence_data['policy'] and data2['policy']) and \
                    presence_data['policy'].id == data2['policy'].id:
                presence_data['_reuse'] = True

            # Calculate the number of days worked in the last week of
            # the previous month. Necessary to calculate Weekly Rest Day OT.
            #
            lsd = last_X_days()
            att_obj = self.env['hr.attendance']
            if len(lsd.arr) == 0:
                d = day_from - timedelta(days=6)
                while d < day_from:
                    att_ids = att_obj.search([
                        ('employee_id', '=', contract.employee_id.id),
                        '|', ('check_in', '=', d.strftime('%Y-%m-%d')),
                        ('check_out', '=', d.strftime('%Y-%m-%d'))])
                    if len(att_ids) > 1:
                        lsd.push(True)
                    else:
                        lsd.push(False)
                    d += timedelta(days=1)

            attendances = {
                'MAX': {
                    'name': _("Maximum Possible Working Hours"),
                    'sequence': 1,
                    'code': 'MAX',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                },
            }
            leaves = {}
            att_obj = self.env['hr.attendance']
            awol_code = False
            import logging
            _l = logging.getLogger(__name__)
            for day in range(0, nb_of_days):
                dtDateTime = datetime.strptime(
                    (day_from + timedelta(days=day)).strftime('%Y-%m-%d'),
                    '%Y-%m-%d')
                rest_days = contract_rest_days
                normal_working_hours = 0

                # Get Presence data
                #
                presence_data = get_presence_policies(
                    contract.policy_group_id, dtDateTime.date(), presence_data)
                presence_policy = presence_data['policy']
                presence_codes = presence_policy and \
                    presence_policy.get_codes() or []
                presence_sequence = 2

                for pcode, pname, ptype, prate, pduration in presence_codes:
                    if attendances.get(pcode, False):
                        continue
                    if ptype == 'normal':
                        normal_working_hours += float(pduration) / 60.0
                    attendances[pcode] = {
                        'name': pname,
                        'code': pcode,
                        'sequence': presence_sequence,
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'rate': prate,
                        'contract_id': contract.id,
                    }
                    presence_sequence += 1

                # Get OT data
                ot_data = get_ot_policies(
                    contract.policy_group_id, dtDateTime.date(), ot_data)
                ot_policy = ot_data['policy']
                daily_ot = ot_data['daily']
                restday2_ot = ot_data['restday2']
                restday_ot = ot_data['restday']
                weekly_ot = ot_data['weekly']
                ot_codes = ot_policy and ot_policy.get_codes() or []
                ot_sequence = 3

                for otcode, otname, ottype, otrate in ot_codes:
                    if attendances.get(otcode, False):
                        continue
                    attendances[otcode] = {
                        'name': otname,
                        'code': otcode,
                        'sequence': ot_sequence,
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'rate': otrate,
                        'contract_id': contract.id,
                    }
                    ot_sequence += 1

                # Get Absence data
                #
                absence_data = get_absence_policies(
                    contract.policy_group_id, dtDateTime.date(), absence_data)
                absence_policy = absence_data['policy']
                absence_codes = absence_policy and absence_policy.get_codes(
                ) or []
                absence_sequence = 50
                for abcode, abname, abtype, abrate, useawol in absence_codes:
                    if leaves.get(abcode, False):
                        continue
                    if useawol:
                        awol_code = abcode
                    if abtype == 'unpaid':
                        abrate = 0
                    elif abtype == 'dock':
                        abrate = -abrate
                    leaves[abcode] = {
                        'name': abname,
                        'code': abcode,
                        'sequence': absence_sequence,
                        'number_of_days': 0.0,
                        'number_of_hours': 0.0,
                        'rate': abrate,
                        'contract_id': contract.id,
                    }
                    absence_sequence += 1

                # For Leave related computations:
                # actual_rest_days: days that are rest days in schedule that
                #  was actualy used scheduled_hours: nominal number of
                # full-time hours for the working day. If the employee is
                # scheduled for this day we use those hours. If not we try
                # to determine the hours he/she would have worked based on
                # the schedule template attached to the contract.

                actual_rest_days = sched_obj.get_rest_days(
                    contract.employee_id.id, dtDateTime)
                scheduled_hours = \
                    sched_detail_obj.scheduled_hours_on_day_from_range(
                        dtDateTime.date(), sched_hours_dict)
                # If the calculated rest days and actual rest days differ, use
                # actual rest days
                if actual_rest_days is not None and len(rest_days) != len(
                        actual_rest_days):
                    rest_days = actual_rest_days
                elif actual_rest_days is not None:
                    for d in actual_rest_days:
                        if d not in rest_days:
                            rest_days = actual_rest_days
                            break

                if scheduled_hours == 0 and dtDateTime.weekday() not in \
                        rest_days:
                    if contract.working_hours:
                        scheduled_hours = \
                            contract.working_hours.get_hours_by_weekday(
                                dtDateTime.weekday())

                # Actual number of hours worked on the day. Based on attendance
                # records.
                working_hours_on_day = self.attendance_dict_hours_on_day(
                    dtDateTime.date(), working_hours_dict)

                # Is today a holiday?
                public_holiday = self.holidays_list_contains(
                    dtDateTime.date(), public_holidays_list)

                # Keep count of the number of hours worked during the week for
                # weekly OT
                if dtDateTime.weekday() == contract.pps_id.ot_week_startday:
                    worked_hours_in_week = working_hours_on_day
                else:
                    worked_hours_in_week += working_hours_on_day

                push_lsd = True
                if working_hours_on_day:
                    done = False

                    if public_holiday:
                        _hours, push_lsd = self._book_holiday_hours(
                            contract, attendances,
                            holiday_obj, dtDateTime, rest_days, lsd,
                            working_hours_on_day)
                        if _hours == 0:
                            done = True
                        else:
                            working_hours_on_day = _hours

                    if not done and restday2_ot:
                        _hours, push_lsd = self._book_restday_hours(
                            contract, presence_policy, ot_policy,
                            attendances, dtDateTime, rest_days, lsd,
                            working_hours_on_day)
                        if _hours == 0:
                            done = True
                        else:
                            working_hours_on_day = _hours

                    if not done and restday_ot:
                        _hours, push_lsd = self._book_weekly_restday_hours(
                            contract, presence_policy, ot_policy,
                            attendances, dtDateTime, rest_days, lsd,
                            working_hours_on_day)
                        if _hours == 0:
                            done = True
                        else:
                            working_hours_on_day = _hours

                    if not done and weekly_ot:
                        # raise osv.except_osv(_('Attendance Error!'),
                        #                      _('There is not a final '
                        #                        'sign-out record for %s on')
                        #                      % (ot_policy.line_ids))
                        for line in ot_policy.line_ids:
                            if line.type == 'weekly' and (
                                not line.weekly_working_days or
                                            line.weekly_working_days == 0):
                                _active_after = float(line.active_after) / 60.0
                                if worked_hours_in_week > _active_after:
                                    if worked_hours_in_week - _active_after \
                                            > working_hours_on_day:
                                        attendances[line.code][
                                            'number_of_hours'] += \
                                            working_hours_on_day
                                    else:
                                        attendances[line.code][
                                            'number_of_hours'] += \
                                            worked_hours_in_week - \
                                            _active_after
                                    attendances[line.code][
                                        'number_of_days'] += 1.0
                                    done = True

                    if not done and daily_ot:

                        # Do the OT between specified times (partial OT)
                        # first, so that it
                        # doesn't get double-counted in the regular OT.
                        partial_hr = 0
                        hours_after_ot = working_hours_on_day
                        for line in ot_policy.line_ids:
                            active_after_hrs = float(line.active_after) / 60.0
                            if line.type == 'daily' and working_hours_on_day \
                                    > active_after_hrs and \
                                    line.active_start_time:
                                partial_hr = att_obj.partial_hours_on_day(
                                    contract, dtDateTime, active_after_hrs,
                                    line.active_start_time,
                                    line.active_end_time, line.tz,
                                    punches_list=self.attendance_dict_list(
                                        working_hours_dict))
                                if partial_hr > 0:
                                    attendances[line.code][
                                        'number_of_hours'] += partial_hr
                                    attendances[line.code][
                                        'number_of_days'] += 1.0
                                    hours_after_ot -= partial_hr

                        for line in ot_policy.line_ids:
                            active_after_hrs = float(line.active_after) / 60.0
                            if line.type == 'daily' and hours_after_ot > \
                                    active_after_hrs and not \
                                    line.active_start_time:
                                attendances[line.code][
                                    'number_of_hours'] += hours_after_ot - (
                                    float(line.active_after) / 60.0)
                                attendances[line.code]['number_of_days'] += 1.0

                    if not done:
                        # raise osv.except_osv(_('Attendance Error!'),
                        #             _('There is not a final sign-out record '
                        #               'for %s on') % (hasattr(
                        #                 presence_policy, 'line_ids')))
                        if hasattr(presence_policy, 'line_ids'):
                            for line in presence_policy.line_ids:
                                if line.type == 'normal':
                                    normal_hours = self._get_applied_time(
                                        working_hours_on_day,
                                        line.active_after,
                                        line.duration)
                                    attendances[line.code][
                                        'number_of_hours'] += normal_hours
                                    attendances[line.code]['number_of_days'] \
                                        += 1.0
                                    done = True
                                    _l.warning('nh: %s', normal_hours)
                                    _l.warning('att: %s', attendances[
                                        line.code])

                    if push_lsd:
                        lsd.push(True)
                else:
                    lsd.push(False)

                leave_type, leave_hours = self.leaves_list_get_hours(
                    contract.employee_id.id,
                    contract.id, contract.working_hours,
                    day_from + timedelta(days=day), leaves_list)

                # Find leave type ID
                lt_data = False
                if leave_type:
                    lt_data = self.env['hr.holidays.status'].search(
                        [('code', '=', leave_type)])
                rest_days_ok = True
                public_holidays_ok = True
                if lt_data:
                    if lt_data.ex_rest_days:
                        if dtDateTime.weekday() in rest_days:
                            rest_days_ok = False
                    if lt_data.ex_public_holidays:
                        if lt_data.ex_public_holidays and public_holiday:
                            public_holidays_ok = False

                if leave_type and rest_days_ok and public_holidays_ok:
                    if leave_type in leaves:
                        leaves[leave_type]['number_of_days'] += 1.0
                        leaves[leave_type]['number_of_hours'] += \
                            (leave_hours > scheduled_hours) and \
                            scheduled_hours or leave_hours
                    else:
                        leaves[leave_type] = {
                            'name': leave_type,
                            'sequence': 8,
                            'code': leave_type,
                            'number_of_days': 1.0,
                            'number_of_hours':
                                (leave_hours > scheduled_hours) and
                                scheduled_hours or leave_hours,
                            'contract_id': contract.id,
                        }
                elif awol_code and \
                        (scheduled_hours > 0 and
                         working_hours_on_day < scheduled_hours) \
                        and not public_holiday:
                    hours_diff = scheduled_hours - working_hours_on_day
                    leaves[awol_code]['number_of_days'] += 1.0
                    leaves[awol_code]['number_of_hours'] += hours_diff

                # Calculate total possible working hours in the month
                if dtDateTime.weekday() not in rest_days:
                    attendances['MAX'][
                        'number_of_hours'] += normal_working_hours
                    attendances['MAX']['number_of_days'] += 1

            leaves = [value for key, value in leaves.items()]
            # ###Tamkeen###
            month_last_day = calendar.monthrange(day_to.year, day_to.month)[1]
            for leave_input in leaves:
                if leave_input['number_of_days']:
                    actual_leave_days = leave_input['number_of_days']
                    if month_last_day == 29 and day_to.month == 2 and \
                            leave_type:
                        actual_leave_days += 1
                    elif month_last_day == 28 and day_to.month == 2 and \
                            leave_type:
                        actual_leave_days += 2
                    elif month_last_day == 31 and actual_leave_days >= 2 and \
                            leave_type:
                        actual_leave_days -= 1
                    elif month_last_day == 31 and actual_leave_days == 1 and \
                            leave_type:
                        actual_leave_days = 0
                    leave_input.update({"number_of_days": actual_leave_days})
            # #############
            attendances = [value for key, value in attendances.items()]
            res += attendances + leaves
        return res
