from odoo import models, api, fields, _
from datetime import datetime

class CertificatesReject(models.TransientModel):
    _name = 'certificates.reject.reason'

    reason = fields.Text('Reason')
    is_reject = fields.Boolean('is Reject')

    @api.multi
    def reject_salary_certificates(self):
        context = dict(self._context) or {}
        if context.get('active_id'):
            certificates_rec = self.env['emp.salary.certificates'].browse(
                context.get('active_id'))
            if self.is_reject:
                certificates_rec.generate_service_log('Hr Approval',
                                                      'Reject', self.reason)
                certificates_rec.state = 'reject'
                certificates_rec.with_context({
                    'reason': self.reason}).send_notification_mail_to(
                    'rejected')

            else:
                certificates_rec.generate_service_log('Hr Approval',
                                                      'Draft', self.reason)
                certificates_rec.state = 'draft'
                certificates_rec.send_notification_mail_to('return')
                certificates_rec.write({'other_dest_org': '',
                                        'other_purpose': '',
                                        'need_to_add_missing_destination':
                                            False,
                                        'need_to_add_missing_purpose': False})