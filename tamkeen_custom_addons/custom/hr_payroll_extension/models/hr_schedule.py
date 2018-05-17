from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DATETIMEFORMAT
from odoo import api, models


# class ScheduleDetail(models.Model):
#     _inherit = "hr.schedule.detail"
#     _description = "Schedule Detail"

    # @api.model
    # def scheduled_begin_end_times_range(self, employee_id, contract_id,
    #                                     dStart, dEnd):
    #     """
    #     Returns a dictionary with the dates in range dtStart - dtEnd as keys
    #     and a list of tuples containing shift start and end times during
    #     those days as values
    #     :return:
    #     """
    #     res = {}
    #     d = dStart
    #     while d <= dEnd:
    #         res.update({d.strftime(OE_DFORMAT): []})
    #         d += timedelta(days=+1)
    #
    #     sched_details = self.search([
    #         ('schedule_id.employee_id.id', '=', employee_id),
    #         ('day', '>=', dStart.strftime(OE_DFORMAT)),
    #         ('day', '<=', dEnd.strftime(OE_DFORMAT))], order='date_start')
    #     if len(sched_details) > 0:
    #         for detail in sched_details:
    #             res[detail.day].append(
    #                 (datetime.strptime(detail.date_start, OE_DATETIMEFORMAT),
    #                  datetime.strptime(detail.date_end, OE_DATETIMEFORMAT))
    #             )
    #     return res
    #
    # @api.model
    # def scheduled_hours_on_day_from_range(self, d, range_dict):
    #     """
    #     :param d: date
    #     :param range_dict:
    #     :return:
    #     """
    #     dtDelta = timedelta(seconds=0)
    #     shifts = range_dict[d.strftime(OE_DFORMAT)]
    #     for start, end in shifts:
    #         dtDelta += end - start
    #     return float(dtDelta.seconds / 60) / 60.0
