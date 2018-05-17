from odoo import api, models


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _get_company(self, uid2=False):
        if not uid2:
            uid2 = self._uid
        user_obj = self.env['res.users']
        user_rec = user_obj.browse(uid2)
        company_id = user_rec.company_id and user_rec.company_id.id
        return company_id or False

    @api.model
    def _get_allowed_attachment_size(self):
        attachment_size = 10  # MB
        company_id = self._get_company()
        if company_id:
            attachment_size = self.env['res.company'].browse(
                company_id).attachment_size
        return attachment_size

    @api.model
    def _get_allowed_mimetype_id(self):
        mimetype_pool = self.env['white.mimetype']
        ids = mimetype_pool.search([('active', '=', 'True')])
        result = [(x.name) for x in ids]
        return result

    @api.model
    def is_allowed_attachment_check(self, attachment):
        # Checking Size have to add
        return True

    @api.model
    def is_allowed_attachment(self, att_data):
        attached_file_size = 0.0
        if att_data:
            attached_file_size = round(
                (len(att_data) / (1024 * 1024)), 2)
        # 10 # MB
        company_allowed_size = self._get_allowed_attachment_size()
        if attached_file_size <= company_allowed_size:
            return True
        else:
            return False
