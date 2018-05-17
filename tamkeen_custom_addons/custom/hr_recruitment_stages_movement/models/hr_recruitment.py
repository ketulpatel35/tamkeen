from datetime import datetime
import time
from openerp.tools.translate import _
from math import floor
from odoo.exceptions import Warning
from odoo import api, fields, models


class ConfirmationEmailSend(models.Model):
    _name = 'confirmation.mail.send'

    name = fields.Many2one('hr.applicant', string='Applicant')

    @api.model
    def default_get(self, field_list):
        res = super(ConfirmationEmailSend, self).default_get(field_list)
        if self._context and self._context.get('active_id'):
            res['name'] = self._context.get('active_id')
        return res

    @api.multi
    def send_confirmation_email(self):
        template_obj = self.env['mail.template']
        for this in self:
            job_application_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'Job Application')], limit=1)
            cv_screening_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'CV Screening')], limit=1)
            interview_progress_rec = self.env['hr.recruitment.stage'].search(
                [('name', '=', 'Interview in Progress')], limit=1)
            # first_interview_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'First Interview')], limit=1)
            under_assessment_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'Under Assessment')], limit=1)
            under_ref_check_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'Under Reference Check')], limit=1)
            # under_job_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'Under Job Offer')], limit=1)
            future_talent_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'Future Talent Pipeline')], limit=1)

            if cv_screening_rec and job_application_rec and \
                this.name.stage_id.id \
                == cv_screening_rec.id and this.name.previous_stage_id.id \
                    == \
                    job_application_rec.id:
                # Add Rec. Manager As followers
                group_obj = self.env['res.groups']
                user_list = []
                for group in group_obj.search([
                        ('name', '=', 'Recruitment Manager')]):
                    for user in group.users:
                        user_list.append(user.id)
                for user_id in user_list:
                    this.name.message_subscribe_users(user_ids=[
                        user_id])
                    # in v8
                    # self.message_subscribe_users(cr, uid, [applicant.id]
                    # , user_ids=[user_id], context=context)

                # send mail to candidate
                template_rec = template_obj.search([('name', '=',
                                                     'CV Screening')])
                if template_rec:
                    template_rec.send_mail(this.name.id)

            if under_assessment_rec and this.name.stage_id.id == \
                    under_assessment_rec.id and \
                    this.name.assessment_required:
                if not this.name.assessmnet_template_id:
                    raise Warning(_('Warning ! \n'
                                    'Please, create or choose an '
                                    'assessment template'))
                # send mail to candidate
                template_rec = template_obj.search([('name', '=',
                                                     'ASSESSMENT')])
                if template_rec and \
                        this.name.assessmnet_template_id:
                    values = template_rec.generate_email(this.name.id)
                    values['subject'] = \
                        this.name.assessmnet_template_id.subject
                    values['body_html'] = values['body_html'] + \
                        this.name. \
                        assessmnet_template_id.body
                    values[
                        'body_html'] += '<p>&nbsp;</p><p>Regards,</p>' \
                                        '<p>Talent Acquisition Team</p>' \
                                        '<p>Human Resources Department' \
                                        '</p><p>&nbsp;</p>'
                    values['body_html'] += \
                        '<p><img ' \
                        'src="http://tamkeentech.sa/sites/all/themes/' \
                        'tamkeen/assets/img/logo-en.png" ' \
                        'alt="" width="122" height="67" /></p>'
                    """values['subject'] = subject
                    values['email_to'] = email_to
                    values['body_html'] = body_html
                    values['body'] = body_html
                    values['res_id'] = False
                    values['subject'] = 'subject'"""
                    mail_mail_obj = self.env['mail.mail']
                    msg_rec = mail_mail_obj.create(values)
                    if msg_rec:
                        msg_rec.send()

            if under_ref_check_rec and this.name.stage_id.id == \
                    under_ref_check_rec.id and not \
                    this.name.reference_ids:
                # send mail to candidate
                template_rec = template_obj.search([
                    ('name', '=', 'UNDER REFERENCE CHECK')])
                if template_rec:
                    template_rec.send_mail(this.name.id)

            if interview_progress_rec and cv_screening_rec and \
                    this.name.stage_id.id == \
                    interview_progress_rec.id and \
                    this.name.previous_stage_id.id == \
                    cv_screening_rec.id:
                # send mail to candidate
                template_rec = template_obj.search([
                    ('name', '=', 'Interview in Progress')])
                if template_rec:
                    template_rec.send_mail(this.name.id)

            if future_talent_rec and this.name.stage_id.id == \
                    future_talent_rec.id:
                # send mail to candidate
                template_rec = template_obj.search([
                    ('name', '=', 'FUTURE TALENT PIPELINE')])
                if template_rec:
                    template_rec.send_mail(this.name.id)

            if this.name.stage_id:
                # stage = self.env['hr.recruitment.stage'].browse(
                #     vals['stage_id'])
                if this.name.stage_id.template_id:
                    # TDENOTE: probably factorize me in a
                    # message_post_with_template generic method FIXME
                    compose_ctx = dict(this.name._context)
                    compose_ctx.update({'active_ids': this.name._ids})
                    compose_rec = self.env[
                        'mail.compose.message'].with_context(
                        compose_ctx).create({
                            'model': self._context.get('model'),
                            'composition_mode': 'mass_mail',
                            'template_id': this.name.stage_id.template_id.id,
                            'post': True,
                            'notify': True,
                        })
                    values = compose_rec.onchange_template_id(
                        this.name.stage_id.template_id.id, 'mass_mail',
                        self._name, False)['value']
                    if values.get('attachment_ids'):
                        values['attachment_ids'] = [
                            (6, 0, values['attachment_ids'])]
                    compose_rec.with_context(compose_ctx).write(values)
                    compose_rec.send_mail()


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    previous_stage_id = fields.Many2one('hr.recruitment.stage',
                                        string='Previous Stage')

    @api.multi
    def _get_house_allowance(self):
        for applicant_rec in self:
            if applicant_rec.salary_proposed != 0.0:
                applicant_rec.housing_allowance = \
                    (applicant_rec.salary_proposed / 1.35) * 0.25

    @api.multi
    def _get_transport_allowance(self):
        for applicant_rec in self:
            if applicant_rec.salary_proposed != 0.0:
                applicant_rec.transport_allowance = \
                    (applicant_rec.salary_proposed / 1.35) * 0.1

    @api.multi
    def _get_basic(self):
        for applicant_rec in self:
            if applicant_rec.salary_proposed != 0.0:
                applicant_rec.basic_salary = (
                    applicant_rec.salary_proposed / 1.35)

    @api.multi
    def confimation_send_email(self):
        return {
            'name': 'Email Confirmation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'confirmation.mail.send',
            'view_id': self.env.ref(
                'hr_recruitment_stages_movement.'
                'view_confirmation_mail_send_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'model': self._name}
        }

    @api.multi
    def _get_gosi(self):
        for applicant_rec in self:
            if applicant_rec.salary_proposed != 0.0 and \
                    applicant_rec.country_id.name == 'Saudi Arabia':
                applicant_rec.gosi_salary = \
                    (((applicant_rec.salary_proposed / 1.35) * 0.25) + (
                        applicant_rec.salary_proposed / 1.35)) * 0.1
            else:
                applicant_rec.gosi_salary = 0.0

    @api.multi
    def _get_net_salary(self):
        for applicant_rec in self:
            if applicant_rec.salary_proposed != 0.0:
                applicant_rec.net_salary = applicant_rec.salary_proposed - \
                    (((
                        applicant_rec.salary_proposed / 1.35) * 0.25) + (
                        applicant_rec.salary_proposed / 1.35)) * 0.1

    @api.multi
    def get_acctual_experience(self):
        total = 0.0
        for applicant_rec in self:
            for line in applicant_rec.experience_ids:
                if line.date_from and line.date_to:
                    start_today = datetime.strptime(line.date_from, "%Y-%m-%d")
                    end_today = datetime.strptime(line.date_to, "%Y-%m-%d")
                    delta = end_today - start_today
                    total += delta.days
            total_years = floor(total / 365.25)
            total_months = floor(total % 365.25 / 30.0)
            applicant_rec.actual_experience_years = total_years
            applicant_rec.actual_experience_months = total_months

    # @api.onchange('salary_proposed', 'maximum_salary')
    # def onchange_proposed_salary(self):
    #     if self.salary_proposed > self.maximum_salary:
    #         raise Warning(_('Programming Error ! '
    #                         'Unable to determine Payroll Register Id.'))

    # @api.onchange('grade')
    # def onchange_grade_level(self):
    #     if self.grade:
    #         if self.grade.policy_group_id:
    #             policy_group = self.grade.policy_group_id
    #             if policy_group.accr_policy_ids:
    #                 policy_group_accrual = policy_group.accr_policy_ids[0]
    #                 if policy_group_accrual.line_ids:
    #                     accrual_lines = policy_group_accrual.line_ids[0]
    #                     if accrual_lines.accrual_rate:
    #                         self.annual_leave_days = \
    #                             accrual_lines.accrual_rate

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        if self.stage_id:
            if self.stage_id.fold:
                self.date_closed = fields.datetime.now()
                self.stage_name_invisible = self.stage_id.name

    @api.multi
    def write(self, vals):
        """
        :param vals: dictionary
        :return:
        """
        # Define template object to send emails
        # template_obj = self.env['mail.template']
        # user_id change: update date_open
        if vals.get('user_id'):
            vals['date_open'] = fields.datetime.now()
        # check max & proposed salary
        for applicant_rec in self:
            if vals.get('salary_proposed') and vals.get(
                'maximum_salary') and vals.get(
                    'salary_proposed') > vals.get('maximum_salary'):
                raise Warning(_('Invalid Input ! \n'
                                'The Maximum salary must be greater than or '
                                'equal the proposed salary.'))
            elif vals.get('maximum_salary'):
                if applicant_rec.salary_proposed > vals.get('maximum_salary'):
                    raise Warning(_('Invalid Input !\n'
                                    'The Maximum salary must be greater than '
                                    'or equal the proposed salary.'))
            elif vals.get('salary_proposed'):
                if vals.get('salary_proposed') > applicant_rec.maximum_salary:
                    raise Warning(_('Invalid Input ! \n'
                                    'The Maximum salary must be greater than '
                                    'or equal the proposed salary.'))
            vals['previous_stage_id'] = applicant_rec.stage_id.id
        # stage_id: track last stage before update
        if 'stage_id' in vals:
            # Get stages ids
            # job_application_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'Job Application')], limit=1)
            # cv_screening_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'CV Screening')], limit=1)
            # interview_progress_rec = self.env['hr.recruitment.stage'].search(
            #     [('name', '=', 'Interview in Progress')], limit=1)
            first_interview_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'First Interview')], limit=1)
            # under_assessment_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'Under Assessment')], limit=1)
            # under_ref_check_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'Under Reference Check')], limit=1)
            under_job_rec = self.env['hr.recruitment.stage'].search([
                ('name', '=', 'Under Job Offer')], limit=1)
            # under_job_accepted_rec = self.env[
            #     'hr.recruitment.stage'].search([
            #     ('name', '=', 'Job Offer Accepted')], limit=1)
            # candidate_rejected_rec = self.env[
            #     'hr.recruitment.stage'].search([
            #     ('name', '=', 'Candidate Rejected')], limit=1)
            # future_talent_rec = self.env['hr.recruitment.stage'].search([
            #     ('name', '=', 'Future Talent Pipeline')], limit=1)

            for applicant_rec in self:
                if not applicant_rec.user_id:
                    raise Warning(_('Warning ! \n'
                                    'Please set application responsible!'))
                # Only recruitment responsible can change application stage
                if applicant_rec.user_id:
                    if applicant_rec.user_id.id != self.env.user.id:
                        raise Warning(_('Warning ! \n'
                                        'You cannot change application stage'))
                    if under_job_rec and applicant_rec.stage_id.id == \
                            under_job_rec.id and applicant_rec.state not in [
                                'approved', 'draft', 'reject', 'send_offer']:
                        raise Warning(_('Warning ! \n'
                                        'You cannot change application stage '
                                        'because the status not '
                                        'approved/rejected'))

                # if moved from Job Application to CV Screening
                # if cv_screening_rec and job_application_rec and vals.get(
                #     'stage_id') == cv_screening_rec.id and \
                #         applicant_rec.stage_id.id == \
                #         job_application_rec.id:
                #     # Add Rec. Manager As followers
                #     group_obj = self.env['res.groups']
                #     user_list = []
                #     for group in group_obj.search([
                #             ('name', '=', 'Recruitment Manager')]):
                #         for user in group.users:
                #             user_list.append(user.id)
                #     for user_id in user_list:
                #         applicant_rec.message_subscribe_users(user_ids=[
                #             user_id])
                #         # in v8
                #         # self.message_subscribe_users(cr, uid,
                # [applicant.id]
                #         # , user_ids=[user_id], context=context)
                #
                #     # send mail to candidate
                #     template_rec = template_obj.search([('name', '=',
                #                                          'CV Screening')])
                #     if template_rec:
                #         template_rec.send_mail(applicant_rec.id)

                # if moved from CV Screening to Interview in Progress
                # if interview_progress_rec and cv_screening_rec and \
                #         vals.get('stage_id') == \
                #         interview_progress_rec.id and \
                #         applicant_rec.stage_id.id == \
                #         cv_screening_rec.id:
                #     # send mail to candidate
                #     template_rec = template_obj.search([
                #         ('name', '=', 'Interview in Progress')])
                #     if template_rec:
                #         template_rec.send_mail(applicant_rec.id)

                # if moved to first interview
                if first_interview_rec and vals.get('stage_id') == \
                        first_interview_rec.id:
                    if applicant_rec.department_id:
                        if applicant_rec.department_id.manager_id:
                            if applicant_rec.department_id.manager_id.user_id:
                                self.message_subscribe_users(user_ids=[
                                    applicant_rec.department_id.
                                    manager_id.user_id.id])
                                mail_values = {
                                    'body': 'Dear Hiring Manager, '
                                            'this application has been '
                                            'transferred to first interview '
                                            'stage',
                                    'record_name': applicant_rec.name,
                                    'no_auto_thread': False,
                                    'notified_partner_ids': [],
                                    'email_from': 'recruitment@tamkeentech.sa',
                                    'partner_ids': [
                                        applicant_rec.department_id.
                                            manager_id.user_id.partner_id.id],
                                    'author_id': 3,
                                    'subject':
                                        u'Application system notification.'}
                                applicant_rec.message_post(
                                    type='comment', subtype='mail.mt_comment',
                                    **mail_values)
                                # template_id = template_obj.search(cr, uid, [
                                # ('name','=','Department Manager Template (
                                # first interview)')])
                                # if template_id:
                                #     mail_message = template_obj.send_mail(
                                # cr,uid,template_id[0],applicant.id)

                                # if moved to Under Assessment
                                # if under_assessment_rec and vals.get
                                # ('stage_id') == \
                                #         under_assessment_rec.id and \
                                #         applicant_rec.assessment_required:
                                #     if not applicant_rec.
                                # assessmnet_template_id:
                                #         raise Warning(_('Warning ! \n'
                                #                         'Please, create
                                # or choose an '
                                #                         'assessment
                                # template'))
                                #     # send mail to candidate
                                #     template_rec = template_obj.search([
                                # ('name', '=',
                                #
                                # 'ASSESSMENT')])
                                #     if template_rec and \
                                #             applicant_rec.assessmnet_template
                                # _id:
                                #         values = template_rec.generate_email
                                # (applicant_rec.id)
                                #         values['subject'] = \
                                #             applicant_rec.assessmnet_templat
                                # e_id.subject
                                #         values['body_html'] = values['body
                                # _html'] + \
                                #             applicant_rec. \
                                #             assessmnet_template_id.body
                                #         values[
                                #             'body_html'] += '<p>&nbsp;</p><p
                                # >Regards,</p>' \
                                #                             '<p>Talent Acquis
                                # ition Team</p>' \
                                #                             '<p>Human Resour
                                # ces Department' \
                                #                             '</p><p>&nbsp;<
                                # /p>'
                                #         values['body_html'] += \
                                #             '<p><img ' \
                                #             'src="https://join.takamol.com.s
                                # a/wp-content/' \
                                #             'themes/llorix-one/images/takamol
                                # _logo.png" ' \
                                #             'alt="" width="122" height="67" /
                                # ></p>'
                                #         """values['subject'] = subject
                                #         values['email_to'] = email_to
                                #         values['body_html'] = body_html
                                #         values['body'] = body_html
                                #         values['res_id'] = False
                                #         values['subject'] = 'subject'"""
                                #         mail_mail_obj = self.env['mail.mail']
                                #         msg_rec = mail_mail_obj.create(value
                                # s)
                                #         if msg_rec:
                                #             msg_rec.send()

                                # if moved to Under Ref. check
                                # if under_ref_check_rec and vals.get('stage_
                                # id') == \
                                #         under_ref_check_rec.id and not \
                                #         applicant_rec.reference_ids:
                                #     # send mail to candidate
                                #     template_rec = template_obj.search([
                                #         ('name', '=', 'UNDER REFERENCE CHECK
                                # ')])
                                #     if template_rec:
                                #         template_rec.send_mail(applicant_rec
                                # .id)

                                # if moved to Job Offer Accepted
                                # if vals.get('stage_id') == under_job_accepte
                                # d_id:
                                #     #send mail to candidate
                                #     template_id = template_obj.search(cr, ui
                                # d, [
                                #         ('name','=','JOB OFFER ACCEPTED')])
                                #     if template_id:
                                #         mail_message = \
                                #             template_obj.send_mail(
                                #                 cr,uid,template_id[0],appli
                                # cant.id)

                                # if moved to Candidate Rejected and before in
                                # terview
                                # if vals.get('stage_id') == candidate_reject
                                # ed_id:
                                #     if applicant.stage_id.id ==
                                #         job_application_id or
                                #         applicant.stage_id.id == cv_screeni
                                # ng_id:
                                # send mail to candidate
                # template_id = template_obj.search(
                # cr, uid, [('name','=','REJECTED BEFORE BEING INTERVIEW')])
                #         if template_id:
                #             mail_message = template_obj.send_mail(
                # cr,uid,template_id[0],applicant.id)
                #
                # # if moved to Candidate Rejected and after interview
                # if vals.get('stage_id') == candidate_rejected_id:
                #     #send mail to candidate
                #     template_id = template_obj.search(cr, uid, [
                # ('name','=','REJECTED AFTER BEING INTERVIEW')])
                #     if template_id:
                #         mail_message = template_obj.send_mail(
                # cr,uid,template_id[0],applicant.id)

                # if moved to Future Talent Pipeline
                # if future_talent_rec and vals.get('stage_id') == \
                #         future_talent_rec.id:
                #     # send mail to candidate
                #     template_rec = template_obj.search([
                #         ('name', '=', 'FUTURE TALENT PIPELINE')])
                #     if template_rec:
                #         template_rec.send_mail(applicant_rec.id)

                # Add Stage log
                stage_log_obj = self.env['hr.applicant.stage.logs']
                today = datetime.strptime(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    "%Y-%m-%d %H:%M:%S")

                if applicant_rec.stage_logs:
                    start_today = datetime.strptime(applicant_rec.stage_logs[
                        -1].date_from,
                        "%Y-%m-%d %H:%M:%S")
                    end_today = today
                    log_duration = end_today - start_today
                    stage_log_rec = stage_log_obj.browse(
                        applicant_rec.stage_logs[-1].id)
                    stage_log_rec.write({'applicant_id': applicant_rec.id,
                                         'date_to': end_today,
                                         'duration': log_duration.days})

                stage_log_obj.create({'applicant_id': applicant_rec.id,
                                      'stage_id': vals.get('stage_id'),
                                      'user_id': applicant_rec._uid,
                                      'date_from': today})

            vals['date_last_stage_update'] = fields.datetime.now()
            # applicant_rec.onchange_stage_id()
            stage_rec = applicant_rec.stage_id.browse(vals.get('stage_id'))
            vals.update({'date_closed': fields.datetime.now(),
                         'stage_name_invisible': stage_rec.name})
            vals['last_stage_id'] = applicant_rec.stage_id.id
        # else:
        #     res = super(HrApplicant, self).write(vals)

        # post processing: if job changed, post a message on the job
        if vals.get('job_id'):
            for applicant_rec in self:
                name = applicant_rec.partner_name if \
                    applicant_rec.partner_name else applicant_rec.name
                hr_job_rec = self.env['hr.job'].browse(vals['job_id'])
                hr_job_rec.message_post(
                    body=_('New application from %s') % name,
                    subtype="hr_recruitment.mt_job_applicant_new")

        # post processing: if stage changed, post a message in the chatter
        # if vals.get('stage_id'):
        #     stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])
        #     if stage.template_id:
        #         # TDENOTE: probably factorize me in a
        #         # message_post_with_template generic method FIXME
        #         compose_ctx = dict(applicant_rec._context)
        #         compose_ctx.update({'active_ids': applicant_rec._ids})
        #         compose_rec = self.env[
        #             'mail.compose.message'].with_context(compose_ctx).create
        # ({
        #                 'model': self._name,
        #                 'composition_mode': 'mass_mail',
        #                 'template_id': stage.template_id.id,
        #                 'post': True,
        #                 'notify': True,
        #             })
        #         values = compose_rec.onchange_template_id(
        #             stage.template_id.id, 'mass_mail', self._name, False)[
        #             'value']
        #         if values.get('attachment_ids'):
        #             values['attachment_ids'] = [
        #                 (6, 0, values['attachment_ids'])]
        #         compose_rec.with_context(compose_ctx).write(values)
        #         compose_rec.send_mail()
        res = super(HrApplicant, self).write(vals)
        return res

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        for applicant_rec in self:
            if not applicant_rec.joining_date:
                raise Warning(_('Warning ! \n'
                                'You must define Expected Joining date'))
            address_id = contact_name = False
            if applicant_rec.partner_id:
                address_id = applicant_rec.partner_id.address_get().get(
                    'contact', False)
                contact_name = applicant_rec.partner_id.name_get()[0][1]
            if applicant_rec.job_id and (applicant_rec.partner_name or
                                         contact_name):
                applicant_rec.job_id.no_of_hired_employee = \
                    applicant_rec.job_id.no_of_hired_employee + 1
                dict(self._context, mail_broadcast=False)
                emp_company_id = self.env['ir.sequence'].next_by_code(
                    'hr.employee')
                emp_dic = {
                    'name': applicant_rec.partner_name or contact_name,
                    'job_id': applicant_rec.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant_rec.department_id.id or False,
                    'address_id': applicant_rec.company_id and
                    applicant_rec.company_id.partner_id and
                    applicant_rec.company_id.partner_id.id or
                    False,
                    'work_email': applicant_rec.department_id and
                    applicant_rec.department_id.company_id and
                    applicant_rec.department_id.company_id.email or False,
                    'work_phone': applicant_rec.department_id and
                    applicant_rec.department_id.company_id and
                    applicant_rec.department_id.company_id.phone or False,
                    'application_id':
                        applicant_rec.id and applicant_rec.id or False,
                    'f_employee_no': emp_company_id or False,
                    'religion': 'muslim',
                    'name_eng': applicant_rec.partner_name_ar or
                                applicant_rec.partner_name or contact_name,
                    'gender': applicant_rec.gender,
                    'marital': applicant_rec.marital,
                    'birthday': applicant_rec.date_of_birth,
                    'personal_mobile_number': applicant_rec.partner_mobile,

                }
                if applicant_rec.identification_type == 'National_ID':
                    emp_dic.update({'identification_id':
                                    applicant_rec.identification_number})
                elif applicant_rec.identification_type == 'Passport_Number':
                    emp_dic.update({'passport_id':
                                    applicant_rec.identification_number})
                elif applicant_rec.identification_type == 'Iqama_Number':
                    emp_dic.update({'iqama_number':
                                    applicant_rec.identification_number})

                emp_rec = self.env['hr.employee'].create(emp_dic)

                # Qualification Table
                qualification_dic = {
                    'source_name': applicant_rec.university or '',
                    'major': applicant_rec.major and
                    applicant_rec.major.name or '',
                    'specialist': applicant_rec.minor or '',
                    'emp_line': emp_rec.id
                }
                qualification = ''
                if applicant_rec.type_id.name == 'High School':
                    qualification = 'highschool'
                elif applicant_rec.type_id.name == 'Bachelor Degree':
                    qualification = 'bachelor'
                elif applicant_rec.type_id.name == 'Master Degree':
                    qualification = 'master'
                elif applicant_rec.type_id.name == 'Doctoral Degree\PhD':
                    qualification = 'ph_d'
                elif applicant_rec.type_id.name == 'Diploma':
                    qualification = 'diploma'

                if qualification and applicant_rec.expect_grad_year and \
                        applicant_rec.expect_grad_month:
                    qualification_dic.update({'qualifications': qualification})
                    qualification_date = datetime.strptime(str(
                        applicant_rec.expect_grad_year) + "-" + str(
                        applicant_rec.expect_grad_month) + "-01", "%Y-%m-%d"
                    ).date()
                    qualification_dic.update(
                        {'qualification_date': qualification_date})
                    self.env[
                        'tamkeen.hr.qualifications'].create(qualification_dic)

                    # qualification_date = datetime.strptime("01-01" + str(
                    # applicant.expect_grad_year), "%Y-%m-%d").date()

                # Experience Table
                exp_list = []
                for line in applicant_rec.experience_ids:
                    exp_list.append({
                        'company_name': line.employer or '',
                        'job_name': line.job_title or '',
                        'date_of_join': line.date_from,
                        'date_of_leave': line.date_to,
                        'responsibility': '',
                        'emp_line': emp_rec.id
                    })

                for dictionary in exp_list:
                    self.env['tamkeen.hr.experiences'].create(dictionary)
                applicant_rec.emp_id = emp_rec.id
                applicant_rec.job_id.message_post(
                    body=_('New Employee %s Hired') %
                    applicant_rec.partner_name if
                    applicant_rec.partner_name else applicant_rec.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")

                # Four email template has to be sent
                template_obj = self.env['mail.template']
                template_recs = template_obj.search(
                    ['|', '|', '|', '|',
                     ('name', '=', 'HR Operations Action Items'),
                     ('name', '=', 'HR Learning and Development Action Items'),
                     ('name', '=',
                      'Administration and Facilities Management Action Items'),
                     ('name', '=', 'IT Support Action Items'),
                     ('name', '=', 'JOB OFFER ACCEPTED')
                     ])
                for template_rec in template_recs:
                    template_rec.send_mail(applicant_rec.id)
            else:
                raise Warning(_('Warning! \n'
                                'You must define an Applied Job and a Contact '
                                'Name for this applicant.'))

    # Overwrite original function to set application id as
    #  default value
    @api.multi
    def action_makeMeeting(self):
        """ This opens Meeting's calendar view to schedule
        meeting on current applicant
            @return: Dictionary value for created Meeting view
        """
        self.ensure_one()
        applicant = self
        applicant_ids = []
        if applicant.partner_id:
            applicant_ids.append(applicant.partner_id.id)
        if applicant.department_id and \
                applicant.department_id.manager_id and \
                applicant.department_id.manager_id.user_id and\
                applicant.department_id.manager_id.user_id.partner_id:
            applicant_ids.append(
                applicant.department_id.manager_id.
                user_id.partner_id.id)
        category = self.env['ir.model.data'].get_object(
            'hr_recruitment', 'categ_meet_interview')
        res = self.env['ir.actions.act_window'].for_xml_id(
            'calendar', 'action_calendar_event')
        res['context'] = {
            'default_partner_ids': applicant_ids,
            'default_user_id': self.env.uid,
            'default_name': applicant.name,
            'default_categ_ids': category and [category.id] or False,
            'default_application_id': applicant.id,
        }
        return res

    # View Scheduled Meeting
    @api.multi
    def action_viewMeeting(self):
        """ This opens Meeting's list view to view schedule meeting on
            current applicant
            @return: Dictionary value for created Meeting view
        """
        res = self.env['ir.actions.act_window'].for_xml_id(
            'hr_recruitment_stages_movement',
            'action_calendar_application_event')
        res['domain'] = "[('application_id', '=', '" + str(self.name) + "' )]"
        return res

    state = fields.Selection([('draft', 'Draft'),
                              ('comp_benefit', 'Compensation & Benefit'),
                              ('rec_manager', 'Waiting Recruitment Manager'),
                              ('manager_app', 'Waiting HR Manager'),
                              ('dep_manager', 'Waiting Department Manager'),
                              ('unit_head', 'Waiting Unit Head'),
                              ('ceo_approval', 'Waiting CEO'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'),
                              ('send_offer', 'Offer Sent'),
                              ],
                             string='Status', readonly=True,
                             track_visibility='onchange', default='draft')
    stage_name_invisible = fields.Char(string='Stage Name Invisible',
                                       default='Job Application')
    joining_date = fields.Date(string='Expected Joining Date')
    reference2 = fields.Char('Offer reference')
    overall_gia = fields.Float('Overall GIA Result')
    qeyas_result = fields.Float('Qeyas Result')
    overall_eng = fields.Float('Overall Eng Result')
    # Salary fields
    housing_allowance = fields.Float(compute='_get_house_allowance',
                                     string='Housing Allowance',
                                     method=True)
    transport_allowance = fields.Float(
        compute='_get_transport_allowance',
        method=True,
        string='Transportation Allowance')
    basic_salary = fields.Float(compute='_get_basic', method=True,
                                string='Basic')
    gosi_salary = fields.Float(compute='_get_gosi', method=True,
                               string='GOSI')
    net_salary = fields.Float(compute='_get_net_salary', method=True,
                              string='Net Package')
    maximum_salary = fields.Float('Maximum Salary')
    current_salary = fields.Float('Current Total Salary')
    grade = fields.Many2one('grade.level', 'Grade')
    annual_leave_days = fields.Float('Annual Leave days')

    # Compensation & Benefits
    compensation_benefits = fields.Selection([
        ('confirm', 'Confirm'), ('modify', 'Modify')],
        string='Compensation & Benefits')
    comp_ben_comments = fields.Text('Comments')

    # Experience
    experience_ids = fields.One2many('hr.applicant.experience',
                                     'applicant_id', 'Experience',
                                     required=True)
    related_experience = fields.Char('Related Experience')
    actual_experience_years = fields.Float('Actual Experience')
    actual_experience_months = fields.Float('Actual Experience Months')

    # Assessment
    assessment_required = fields.Boolean("Assessment Required",
                                         default=True)
    assessmnet_template_id = fields.Many2one(
        'hr.applicant.assessment.template', 'Template')

    # Approval log table
    approval_logs = fields.One2many('hr.applicant.logs', 'applicant_id',
                                    'Approval Logs', readonly=True)
    # Stage log table
    stage_logs = fields.One2many('hr.applicant.stage.logs',
                                 'applicant_id', 'Stage Logs',
                                 readonly=True)

    # Note: method was commented because, Required record(s) not available.
    # Ex: return 'hr_recruitment_stages_movement.mt_draft' --> mt_draft
    # @api.multi
    # def _track_subtype(self, init_values):
    #     #  used to track events
    #     self.ensure_one()
    #     if 'state' in init_values and self.state == 'draft':
    #         return 'hr_recruitment_stages_movement.mt_draft'
    #     if 'state' in init_values and self.state == 'comp_benefit':
    #         return 'hr_recruitment_stages_movement.mt_comp_benefit'
    #     if 'state' in init_values and self.state == 'rec_manager':
    #         return 'hr_recruitment_stages_movement.mt_rec_manager'
    #     if 'state' in init_values and self.state == 'manager_app':
    #         return 'hr_recruitment_stages_movement.mt_manager_app'
    #     if 'state' in init_values and self.state == 'dep_manager':
    #         return 'hr_recruitment_stages_movement.mt_dep_manager'
    #     if 'state' in init_values and self.state == 'unit_head':
    #         return 'hr_recruitment_stages_movement.mt_unit_head'
    #     if 'state' in init_values and self.state == 'ceo_approval':
    #         return 'hr_recruitment_stages_movement.mt_ceo_manager'
    #     if 'state' in init_values and self.state == 'approved':
    #         return 'hr_recruitment_stages_movement.mt_approved'
    #     if 'state' in init_values and self.state == 'reject':
    #         return 'hr_recruitment_stages_movement.mt_reject'
    #     return super(HrApplicant, self)._track_subtype(init_values)

    @api.multi
    def get_web_base_url(self):
        """
        method call from email templets.
        :return:
        """
        config_obj = self.env['ir.config_parameter']
        config_rec = config_obj.search([('key', '=', 'web.base.url.static')])
        if config_rec:
            return config_rec[0].value
        return False

    @api.multi
    def send_to_approve(self):
        self.env['calendar.event'].search([
            ('application_id', '=', self._ids[0])])
        emails_list = []
        for group_rec in self.env['res.groups'].search(
                [('name', '=', 'Compensation and Benefits')]):
            for user_rec in group_rec.users:
                if user_rec.employee_ids and user_rec.employee_ids[0].work_email:
                    emails_list.append(user_rec.employee_ids[0].work_email)

        for applicant_rec in self:
            if not applicant_rec.user_id:
                raise Warning(_('Warning! \n'
                                'Please the responsible'))
            if not applicant_rec.partner_name:
                raise Warning(_('Warning! \n'
                                'Please set candidate name'))
            # if applicant_rec.salary_proposed == 0.0:
            #     raise Warning(_('Warning! \n'
            #                     'Please set proposed salary'))
            if not applicant_rec.email_from:
                raise Warning(_('Warning! \n'
                                'Please set candidate email'))
            # if not applicant_rec.grade:
            #     raise Warning(_('Warning! \n'
            #                     'Please set the grade'))
            # if not meeting_ids:
            #     raise Warning(_('Warning! \n'
            #                     'Please set Interview for the candidate'))

            # Add Log Record
            approval_log_obj = self.env['hr.applicant.logs']
            today = datetime.strptime(
                time.strftime("%Y-%m-%d %H:%M:%S"),
                "%Y-%m-%d %H:%M:%S")
            approval_log_obj.create({
                'applicant_id': applicant_rec.id,
                'name': 'Requisition Owner',
                'approval': 'Approved',
                'user_id': applicant_rec._uid,
                'date': today})
            # Send email to all group users
            self.send_mail('Compensation and Benefit Template', emails_list)
            applicant_rec.state = 'comp_benefit'
            #     if msg_id:
            #         mail_mail_obj.send(cr, uid, [msg_id], context=context)
            #
            # #             mail_values = {'body': 'This application is waiting
            #     your approval.',  'record_name': applicant.name,
            #     'no_auto_thread': False, 'notified_partner_ids':[],
            # #                            'email_from': 'ta@TakaMoL.com.sa',
            #     'partner_ids': [134],
            # #                            'author_id': 3, 'subject':
            #     u'Application system notification.'}
            # #             self.message_post(cr, uid, [ids[0]], type='email',
            #     subtype='mail.mt_comment', context=context, **mail_values)
            #
            # #         group_obj = self.pool.get('res.groups')
            # #         group_id = group_obj.search(cr, uid, [
            #     ('name','=','Recruitment Manager')])
            # #         for group in group_obj.browse(
            #     cr, uid, group_id, context=context):
            # #             user_list = []
            # #             for user in group.users:
            # #                 user_list.append(user.id)
            # #         template_id = template_obj.search(
            #     cr, uid, [('name','=','Recruitment Manager Template')])
            # #         for applicant in self.browse(
            #     cr, uid, ids, context=context):
            # #             if template_id and user_list:
            # #                 for user_id in user_list:
            # #                     self.message_subscribe_users(
            #     cr, uid, [applicant.id], user_ids=[user_id], context=context)
            # #
            # #                 mail_message = template_obj.send_mail(
            #     cr,uid,template_id[0],applicant.id)
            # #                 values = template_obj.generate_email(
            #     cr, uid, template_id[0], ids[0], context=context)
            # #                 values['notification'] = True
            # #                 mail_mail_obj = self.pool.get('mail.mail')
            # #                 msg_id = mail_mail_obj.create(
            #     cr, uid, values, context=context)
            # #                 if msg_id:
            # #                     mail_mail_obj.send(
            #     cr, uid, [msg_id], context=context)
            # #                mail_message = template_obj.send_mail(
            #     cr,uid,template_id[0],applicant.id)

    @api.multi
    def print_off_letter(self):
        for applicant_rec in self:
            if applicant_rec.country_id.name == "Saudi Arabia":
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name':
                        'hr_recruitment_stages_movement.'
                        'local_candidate_template',
                }
            else:
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'hr_recruitment_stages_movement.'
                                   'employment_summary_temp',
                }
        return True


class HrApplicantLogs(models.Model):
    _name = 'hr.applicant.logs'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant',
                                   required=True, readonly=True,
                                   ondelete="cascade")
    name = fields.Char('Action')
    approval = fields.Char('Approval')
    user_id = fields.Many2one('res.users', 'By')
    date = fields.Datetime('Date/Time')


class HrApplicantStageLogs(models.Model):
    _name = 'hr.applicant.stage.logs'

    applicant_id = fields.Many2one('hr.applicant', 'Applicant',
                                   required=True, readonly=True,
                                   ondelete="cascade")
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage')
    user_id = fields.Many2one('res.users', 'By')
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    duration = fields.Float('Duration(Days)')


class HrApplicantAssessmentTemplate(models.Model):
    _name = 'hr.applicant.assessment.template'

    name = fields.Char('Template Name')
    subject = fields.Char('Subject')
    body = fields.Text('Body')


class HrApplicantExperience(models.Model):
    _name = 'hr.applicant.experience'

    @api.onchange('current_job')
    def onchange_current_job(self):
        if self.current_job:
            self.date_to = time.strftime('%Y-%m-%d')

    applicant_id = fields.Many2one('hr.applicant', 'Applicant',
                                   required=True, readonly=True,
                                   ondelete="cascade")
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    job_title = fields.Char('Job Title')
    employer = fields.Char('Employer')
    current_job = fields.Boolean("Current Job")
