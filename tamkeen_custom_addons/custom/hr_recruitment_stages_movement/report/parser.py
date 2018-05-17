from odoo.report import report_sxw
from odoo import models
from odoo.api import Environment


class ReportParser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ReportParser, self).__init__(
            cr, uid, name, context=context)
        self._cr, self._uid, self._context = cr, uid, context
        self.localcontext.update({
            'get_basic': self.get_basic,
            'get_total': self.get_total,
            'get_interview_details': self.get_interview_details,
            'get_recent_job': self.get_recent_job,
        })

    def get_basic(self, salary, house, transport):
        return salary - round(house, 0) - round(transport, 0)

    def get_total(self, salary, house, transport):
        return self.get_basic(
            salary, house, transport) + round(
            house, 0) + round(transport, 0)

    def get_interview_details(self, application_rec):
        res = {}
        attendee_list = []
        sorted_list = []
        self.env = Environment(self._cr, self._uid, self._context)
        calendar_obj = self.env['calendar.event']
        meeting_rec = calendar_obj.search([('application_id', '=',
                                            application_rec.id)])
        for meeting in meeting_rec:
            sorted_list.append(meeting.start_date)
        sorted_list.sort()
        #        raise osv.except_osv(('Invalid Input!'), sorted_list)
        for date in sorted_list:
            for meeting in meeting_rec:
                if meeting.start_date == date:
                    for attendee in meeting.attendee_ids:
                        name = ''
                        if attendee.partner_id:
                            name = attendee.partner_id.name
                        res = {
                            'interview': meeting.name,
                            'interviewer': name,
                            'date': meeting.start_date,
                            'recommendation': attendee.recommendation,
                        }
                        attendee_list.append(res)
        return attendee_list

    def get_recent_job(self, experience_ids):
        res = {'job': '', 'employer': ''}
        sorted_list = []
        for line in experience_ids:
            sorted_list.append(line.date_from)
        if sorted_list:
            sorted_list.sort()
            last_date = sorted_list[-1]
            for line in experience_ids:
                if last_date == line.date_from:
                    res = {'job': line.job_title, 'employer': line.employer}
        return res


class LocalCandidateReport(models.AbstractModel):
    _name = 'report.hr_recruitment_stages_movement.local_candidate_template'

    _inherit = 'report.abstract_report'

    _template = 'hr_recruitment_stages_movement.local_candidate_template'

    _wrapped_report_class = ReportParser


class ExpatCandidateReport(models.AbstractModel):
    _name = 'report.hr_recruitment_stages_movement.expat_candidate_template'

    _inherit = 'report.abstract_report'

    _template = 'hr_recruitment_stages_movement.expat_candidate_template'

    _wrapped_report_class = ReportParser


class EmploymentSummaryReport(models.AbstractModel):
    _name = 'report.hr_recruitment_stages_movement.employment_summary_temp'

    _inherit = 'report.abstract_report'

    _template = 'hr_recruitment_stages_movement.employment_summary_temp'

    _wrapped_report_class = ReportParser


class EmploymentSummaryReport(models.AbstractModel):
    _name = 'report.hr_recruitment_stages_movement.emp_sum_dep_manager_temp'

    _inherit = 'report.abstract_report'

    _template = 'hr_recruitment_stages_movement.emp_sum_dep_manager_temp'

    _wrapped_report_class = ReportParser
