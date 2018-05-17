from openerp import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_reg_id = fields.Many2one('vendor.registration',
                                    string='Vendor Registration')
    comment = fields.Text(string='Notes', track_visibility='always')
    commercial_registration = fields.Char('Commercial Registration#')
    commercial_registration_expiry_date = fields.Date(
        'Commercial Registration Expiry Date')

    @api.multi
    def set_active_inactive(self):
        """
        vendor black list
        :return:
        """
        view = self.env.ref(
            'vendor_registration.blacklist_vendor_form_view')
        if not view:
            return True
        return {
            'name': _('Blacklist Reason'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'blacklist.vendor',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


