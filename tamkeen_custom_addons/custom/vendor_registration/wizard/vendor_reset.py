from openerp import models, api, fields
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class VendorRegistrationreste(models.Model):
    _name = 'vendor.registration.reset'
    _description = 'Reset'

    @api.multi
    def _get_today_time(self):
        return datetime.now().strftime(OE_DTFORMAT)
    name = fields.Char('Reason For Reset')
    reset_date = fields.Datetime(string='Reset Date',
                                 readonly=True,
                                 copy=False,
                                 default=_get_today_time)

    @api.multi
    def reset_request(self):
        if self._context.get('active_id'):
            vendor_obj = self.env['vendor.registration'].search([
                ('id', '=', self._context.get('active_id'))])
            if vendor_obj:
                vendor_obj.reset_user_id = self.env.user.id
                vendor_obj.reset_reason = self.name
                vendor_obj.reset_date = self.reset_date
                vendor_obj.state = 'draft'
                # For reset all approvals Fields
                vendor_obj.reviewd_user_id = False
                vendor_obj.review_date = False
                vendor_obj.evaluated_user_id = False
                vendor_obj.evaluated_date = False
                vendor_obj.holded_user_id = False
                vendor_obj.holded_date = False
                vendor_obj.shortlisted_user_id = False
                vendor_obj.shortlisted_date = False
                vendor_obj.registered_user_id = False
                vendor_obj.registered_date = False
