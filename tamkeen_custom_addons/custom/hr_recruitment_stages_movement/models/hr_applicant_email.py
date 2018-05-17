from odoo import api, fields, models, sql_db, SUPERUSER_ID
import threading
import json
import time
import logging

SEP = ';'

_logger = logging.getLogger(__name__)


class HRApplicantEmail(models.Model):
    _name = "hr.applicant.email"

    applicant_id = fields.Many2one(
        'hr.applicant',
        required=True,
        readonly=True,
        ondelete="cascade")
    user_id = fields.Many2one('res.users', required=True)
    template_name = fields.Char(required=True)
    emails_list = fields.Char()
    test_email = fields.Char()
    context = fields.Char()
    processed = fields.Boolean(default=False, required=True, index=True)
    processed_time = fields.Datetime()
    error = fields.Char()
    state = fields.Char()

    def __init__(self, pool, cr):
        super(HRApplicantEmail, self).__init__(pool, cr)
        cr.execute(
            "SELECT 1 FROM information_schema.tables "
            "where table_name ='hr_applicant_email'")
        if cr.fetchone():
            cr.execute(
                "select id from hr_applicant_email where processed = false and"
                " create_date > (now() - INTERVAL '2 day')")
            ids = [row[0] for row in cr.fetchall()]
            for record_id in ids:
                thread = HRApplicantEmailThread(
                    cr.dbname, record_id, delay_start=True)
                thread.start()

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if vals.get('emails_list', []):
            vals['emails_list'] = SEP.join(vals.get('emails_list', []))
            vals['context'] = json.dumps(vals.get('context'))
        res = super(HRApplicantEmail, self).create(vals)
        thread = HRApplicantEmailThread(self.env.cr.dbname, res.id)
        thread.start()
        return res


class HRApplicantEmailThread(threading.Thread):
    def __init__(self, dbname, hr_applicant_email_id, delay_start=False):
        super(
            HRApplicantEmailThread, self).__init__(
            name='%s hr.applicant.email %s' %
                 (dbname, hr_applicant_email_id))
        self.dbname = dbname
        self.hr_applicant_email_id = hr_applicant_email_id
        self.delay_start = delay_start

    def run(self):
        if self.delay_start:
            time.sleep(10)
        _logger.info('Start ' + self.name)
        # mail_msg_obj = self.env['mail.message']
        # subtype_id = self.env['mail.message.subtype'].search([
        #     ('name', '=', 'Discussions')], limit=1)
        # mail_msg_obj.create({'subject': self.name + 'Warning',
        #                      'body': 'Start ' + self.name,
        #                      'model': 'mail.channel',
        #                      'res_id': 1,
        #                      'message_type': 'notification',
        #                      'record_name': 'general',
        #                      'subtype_id': subtype_id.id or False,
        #                      'channel_ids': [
        #                          (6, 0,
        #                           self.message_channel_ids.ids)
        #                      ]})
        db = sql_db.db_connect(self.dbname)
        with db.cursor() as cr:
            with api.Environment.manage():
                context = {}
                env = api.Environment(cr, SUPERUSER_ID, context)
                applicant_email = None
                counter = 0
                while not applicant_email and counter < 30:
                    time.sleep(1)
                    applicant_email = env['hr.applicant.email'].browse(
                        self.hr_applicant_email_id)
                    counter += 1
                if not applicant_email:
                    mail_msg_obj = self.env['mail.message']
                    subtype_id = self.env['mail.message.subtype'].search([
                        ('name', '=', 'Discussions')], limit=1)
                    mail_msg_obj.create({'subject': self.name + 'Warning',
                                         'body': 'hr.applicant.email %s not '
                                                 'found ' %
                                                 self.hr_applicant_email_id,
                                         'model': 'mail.channel',
                                         'res_id': 1,
                                         'message_type': 'notification',
                                         'record_name': 'general',
                                         'subtype_id': subtype_id.id or False,
                                         'channel_ids': [
                                             (6, 0,
                                              self.message_channel_ids.ids)
                                         ]})
                    return
                # context.update(json.loads(applicant_email.context))
                error = ''
                try:
                    emails = \
                        applicant_email.test_email or \
                        applicant_email.emails_list
                    applicant_email.applicant_id.process_send_mail(
                        applicant_email.template_name, emails.split(SEP))
                except Exception as e:
                    _logger.exception(e)
                    # mail_msg_obj = self.env['mail.message']
                    # subtype_id = self.env['mail.message.subtype'].search([
                    #     ('name', '=', 'Discussions')], limit=1)
                    # # mail_msg_obj.create({'subject': 'Exception',
                    #                      'body': e,
                    #                      'model': 'mail.channel',
                    #                      'res_id': 1,
                    #                      'message_type': 'notification',
                    #                      'record_name': 'general',
                    #                      'subtype_id': subtype_id.id or False
                    #                      })
                    error = str(e)
                applicant_email.write(
                    dict(
                        processed=True,
                        processed_time=fields.Datetime.now(),
                        error=error))
                cr.commit()
        _logger.info('Finish ' + self.name)
        # mail_msg_obj = self.env['mail.message']
        # subtype_id = self.env['mail.message.subtype'].search([
        #     ('name', '=', 'Discussions')], limit=1)
        # mail_msg_obj.create({'subject': self.name + 'Information',
        #                      'body': 'Finish ' + self.name,
        #                      'model': 'mail.channel',
        #                      'res_id': 1,
        #                      'message_type': 'notification',
        #                      'record_name': 'general',
        #                      'subtype_id': subtype_id.id or False,
        #                      'channel_ids': [
        #                          (6, 0,
        #                           self.message_channel_ids.ids)
        #                      ]})
