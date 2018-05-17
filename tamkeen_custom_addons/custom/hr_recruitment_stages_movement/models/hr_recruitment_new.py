from odoo import api, fields, models
from openerp.tools import config
import threading
from datetime import datetime
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


def duplication_check(method):
    """
        not allowed method to be called twice
    """

    # _logger.info('check ' + method.__name__)

    def wrapper(self, *arg, **keywrds):
        if hasattr(self, '_ids') and len(self) == 1:
            call_id = (method.__name__, self.id)
            # _logger.info(
            #     'calling %s thread=%s thead_id=%s' %
            #     (method.__name__, threading.currentThread(), id(
            #         threading.currentThread())))
            mail_msg_obj = self.env['mail.message']
            subtype_id = self.env['mail.message.subtype'].search([
                ('name', '=', 'Discussions')], limit=1)
            mail_msg_obj.create({'subject': 'Information',
                                 'body': 'calling %s thread=%s thead_id=%s' %
                                         (method.__name__,
                                          threading.currentThread(), id(
                                              threading.currentThread())),
                                 'model': 'mail.channel',
                                 'res_id': 1,
                                 'message_type': 'notification',
                                 'record_name': 'general',
                                 'subtype_id': subtype_id.id or False,
                                 })
            # traceback.print_stack()
            # time.sleep(10)
            if getattr(
                    threading.currentThread(),
                    'applicant_method_called',
                    None) == call_id:
                # _logger.info('duplicate call %s' % str(call_id))
                mail_msg_obj = self.env['mail.message']
                subtype_id = self.env['mail.message.subtype'].search([
                    ('name', '=', 'Discussions')], limit=1)
                mail_msg_obj.create({'subject': 'Information',
                                     'body': 'duplicate call %s' % str(
                                         call_id),
                                     'model': 'mail.channel',
                                     'res_id': 1,
                                     'message_type': 'notification',
                                     'record_name': 'general',
                                     'subtype_id': subtype_id.id or False,
                                     })
                return None
            setattr(
                threading.currentThread(),
                'applicant_method_called',
                call_id)
        return method(self, *arg, **keywrds)

    return wrapper


class hr_applicant(models.Model):
    _inherit = "hr.applicant"

    partner_name_ar = fields.Char("Applicant's Arabic Name")

    def insert_log(self, name='', approval=''):
        self.env['hr.applicant.logs'].create(
            {
                'applicant_id': self.id,
                'name': name,
                'approval': approval,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now()
            })

    @api.multi
    def create_employee_from_applicant(self):
        self.ensure_one()
        res = super(hr_applicant, self).create_employee_from_applicant()
        self.send_mail('Job Offer Accepted')
        return res

    @duplication_check
    @api.multi
    def send_to_approve(self):
        return super(hr_applicant, self).send_to_approve()

    @duplication_check
    @api.multi
    def rec_manager_confirm(self):
        emails_list = []
        for group_rec in self.env['res.groups'].search(
                [('name', '=', 'HR Manager - Recruitment')]):
            for user_rec in group_rec.users:
                if user_rec.employee_ids:
                    emails_list.append(user_rec.employee_ids[0].work_email)
        for applicant_rec in self:
            # Add Log Record
            approval_log_obj = self.env['hr.applicant.logs']
            today = datetime.strptime(
                time.strftime(OE_DTFORMAT),
                OE_DTFORMAT)
            approval_log_obj.create({'applicant_id': applicant_rec.id,
                                     'name': 'Sr. Manager, TA',
                                     'approval': 'Approved',
                                     'user_id': applicant_rec._uid,
                                     'date': today
                                     })
            # Send email to all group users
            self.send_mail('HR Manager Template', emails_list)
            applicant_rec.state = 'manager_app'

    @duplication_check
    @api.multi
    def unit_head_confirm(self):
        """
        :return:
        """
        emails_list = []
        for group_rec in self.env['res.groups'].search(
                [('name', '=', 'CEO - Recruitment')]):
            for user_rec in group_rec.users:
                if user_rec.employee_ids:
                    emails_list.append(user_rec.employee_ids[0].work_email)
        for applicant_rec in self:
            # Add Log Record
            approval_log_obj = self.env['hr.applicant.logs']
            today = datetime.strptime(
                time.strftime(OE_DTFORMAT),
                OE_DTFORMAT)
            approval_log_obj.create({'applicant_id': applicant_rec.id,
                                     'name': 'Head of Unit',
                                     'approval': 'Approved',
                                     'user_id': applicant_rec._uid,
                                     'date': today})
            # Send email to all group users
            applicant_rec.send_mail('CEO Template', emails_list)
            applicant_rec.state = 'ceo_approval'

    @duplication_check
    @api.multi
    def ceo_manager_confirm(self):
        # Add Log Record
        for applicant_rec in self:
            approval_log_obj = self.env['hr.applicant.logs']
            today = datetime.strptime(
                time.strftime(OE_DTFORMAT),
                OE_DTFORMAT)
            approval_log_obj.create({'applicant_id': applicant_rec.id,
                                     'name': 'CEO', 'approval': 'Approved',
                                     'user_id': self._uid, 'date': today})
            applicant_rec.state = 'approved'

    @duplication_check
    @api.multi
    def refuses(self):
        """
        :return:
        """
        action = ""
        approval_log_obj = self.env['hr.applicant.logs']
        for applicant_rec in self:
            if applicant_rec.state == "rec_manager":
                action = 'Sr. Manager, TA'
            elif applicant_rec.state == "manager_app":
                action = 'Director, HR'
            elif applicant_rec.state == "dep_manager":
                action = 'Hiring Manager'
            elif applicant_rec.state == "unit_head":
                action = 'Head of Unit'
            elif applicant_rec.state == "ceo_approval":
                action = 'CEO'
            # Add Log Record
            today = datetime.strptime(
                time.strftime(OE_DTFORMAT),
                OE_DTFORMAT)
            approval_log_obj.create({'applicant_id': applicant_rec.id,
                                     'name': action,
                                     'approval': 'Rejected',
                                     'user_id': applicant_rec.id,
                                     'date': today})
            applicant_rec.state = 'reject'

    @duplication_check
    @api.multi
    def rest_to_draft_fun(self):
        """
        :return:
        """
        self.ensure_one()
        self.insert_log('Reset To Draft', ' ')
        for applicant_rec in self:
            applicant_rec.state = 'draft'

    @duplication_check
    @api.multi
    def comp_benefit_confirm(self):
        """
        :return:
        """
        self.ensure_one()
        if self.state == 'rec_manager':
            # _logger.warning('comp_benefit_confirm : state already rec_manager
            # ')
            mail_msg_obj = self.env['mail.message']
            subtype_id = self.env['mail.message.subtype'].search([
                ('name', '=', 'Discussions')], limit=1)
            mail_msg_obj.create({'subject': 'Warning',
                                 'body': 'comp_benefit_confirm : state '
                                         'already rec_manager',
                                 'model': 'mail.channel',
                                 'res_id': 1,
                                 'message_type': 'notification',
                                 'record_name': 'general',
                                 'subtype_id': subtype_id.id or False,
                                 })

            return True
        emails_list = []
        for group_rec in self.env['res.groups'].search(
                [('name', '=', 'Recruitment Manager')]):
            for user_rec in group_rec.users:
                if user_rec.employee_ids:
                    emails_list.append(user_rec.employee_ids[0].work_email)
        self.insert_log('Sr. Manager, C&B', 'Approved')
        # Send email to all group users
        self.send_mail('Recruitment Manager Template', emails_list)
        # return self.write({'state': 'rec_manager'})
        self.state = 'rec_manager'
        return True

    @duplication_check
    @api.multi
    def hr_manager_confirm(self):
        self.ensure_one()
        self.insert_log('Director, HR', 'Approved')
        if self.department_id.manager_id.user_id:
            self.message_subscribe_users(
                user_ids=[self.department_id.manager_id.user_id.id])
        self.send_mail('Department Manager Template')
        self.state = 'dep_manager'
        return True

    def get_email(self, email):
        return config.get('oi_test_email') or email

    @duplication_check
    @api.multi
    def dep_manager_confirm(self):
        self.ensure_one()
        self.insert_log('Hiring Manager', 'Approved')
        if self.department_id.manager_id.parent_id:
            if self.department_id.manager_id.parent_id.user_id:
                self.message_subscribe_users(
                    user_ids=[
                        self.department_id.manager_id.parent_id.user_id.id])
        self.send_mail('Unit Head Template')
        self.state = 'unit_head'
        return True

    @duplication_check
    @api.multi
    def candidate_reject(self):
        self.ensure_one()
        if self.env['calendar.event'].search(
                [('application_id', '=', self.id)]):
            template_name = 'REJECTED AFTER BEING INTERVIEW'
        else:
            template_name = 'REJECTED BEFORE BEING INTERVIEW'
        self.stage_id = self.env['hr.recruitment.stage'].search(
            [('name', '=', 'Candidate Rejected')])
        self.send_mail(template_name)
        return True

    @duplication_check
    @api.multi
    def send_off_letter(self):
        self.ensure_one()
        if not self.reference2:
            reference = self.env[
                'ir.sequence'].next_by_code('hr.applicant')
            self.reference2 = reference
        if self.email_from \
                and self.country_id.name == "Saudi Arabia":
            self.send_mail('Send Offer Letter (Saudi)')
        if self.email_from \
                and self.country_id.name != "Saudi Arabia":
            self.send_mail('Send Offer Letter (Non-Saudi)')
        return self.write({'state': 'send_offer'})

    @api.multi
    def send_mail(self, template_name, emails_list=[]):
        self.ensure_one()
        vals = {
            'applicant_id': self.id,
            'user_id': self.env.user.id,
            'state': self.state,
            'template_name': template_name,
            'emails_list': emails_list,
            'test_email': config.get('oi_test_email'),
        }
        self.env['hr.applicant.email'].create(vals)
        return True

    @api.multi
    def process_send_mail(self, template_name, emails_list):
        self.ensure_one()
        template_rec = self.env['mail.template'].search(
            [('name', '=', template_name)], limit=1)
        if not template_rec:
            # _logger.warning('email.template not found %s' % template_name)
            mail_msg_obj = self.env['mail.message']
            subtype_id = self.env['mail.message.subtype'].search([
                ('name', '=', 'Discussions')], limit=1)
            mail_msg_obj.create({'subject': 'Warning',
                                 'body': 'email.template not found %s' %
                                         template_name,
                                 'model': 'mail.channel',
                                 'res_id': 1,
                                 'message_type': 'notification',
                                 'record_name': 'general',
                                 'subtype_id': subtype_id.id or False,
                                 })
            return
        values = template_rec.generate_email(self.id)
        emails_list = emails_list + values.get(
            'email_to', '').replace(',', ';').split(';')
        values['email_to'] = ';'.join(emails_list)
        values['subject'] = '%s (%s - %s)' % (
            values['subject'].strip(), self.partner_name.strip(),
            self.department_id.name)
        # Add report in attachments
        attachment_ids = []
        ir_attachment = self.env['ir.attachment']
        attachments = values.pop('attachments', [])
        mail = self.env['mail.mail'].create(values)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas_fname': attachment[0],
                'datas': attachment[1],
                'res_model': 'mail.message',
                'res_id': mail.mail_message_id.id,
            }

            attachment_ids.append(ir_attachment.create(attachment_data).id)
        if attachment_ids:
            mail.write({'attachment_ids': [(6, 0, attachment_ids)]})
        if mail:
            mail.send()
        return True
