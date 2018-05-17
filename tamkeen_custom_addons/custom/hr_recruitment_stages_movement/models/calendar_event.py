from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    application_id = fields.Many2one('hr.applicant', 'Application',
                                     required=False)

    def getmeeting_invitation_subject(self):
        """
        method call from email templet(s) for get email subject.
        :return:
        """
        if self.application_id and self.application_id.partner_name:
            return '%s  Interview notification (Candidate: %s, %s)' % (
                self.name,
                self.application_id.partner_name.strip(),
                self.application_id.job_id.name)
        return self.name


class CalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    @api.multi
    def _check_recommendation_value(self):
        for record in self:
            if record.recommendation >= 0.0 and record.recommendation <= 10.0:
                return True
            else:
                return False
        return True

    # @api.constraints('recommendation')
    # def _check_recommendation_value(self):
    #     for record in self:
    #         if record.recommendation >= 0.0 and \
    #                         record.recommendation <= 10.0:
    #             return True
    #         else:
    #             raise Warning(_('Warning ! \nPlease enter value between 0.0 '
    #                             'and 10.0'))
    #     return True

    recommendation = fields.Float('Recommendation')

    _constraints = [
        (_check_recommendation_value,
         'Please enter value between 0.0 and 10.0".', ['recommendation']),
    ]

    @api.multi
    def _send_mail_to_attendees(
            self,
            template_xmlid='calendar.calendar_template_meeting_invitation'):
        for record in self:
            if record.event_id.application_id:
                template_xmlid = 'calendar.applicant_interview_invitation'
                break
        return super(CalendarAttendee, self)._send_mail_to_attendees(
            template_xmlid=template_xmlid)
