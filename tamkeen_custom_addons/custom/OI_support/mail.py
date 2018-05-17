# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools import config


config['publisher_warranty_url'] = ''


class publisher_warranty_contract(models.AbstractModel):
    _name = 'publisher_warranty.contract'
    _description = 'Publisher warranty contract'

    @api.model
    def update_notification(self):
        # _logger.info("NO More Spying Stuff")
        mail_msg_obj = self.env['mail.message']
        subtype_id = self.env['mail.message.subtype'].search([
            ('name', '=', 'Discussions')], limit=1)
        mail_msg_obj.create({'subject': 'Information',
                             'body': "NO More Spying Stuff",
                             'model': 'mail.channel',
                             'res_id': 1,
                             'message_type': 'notification',
                             'record_name': 'general',
                             'subtype_id': subtype_id.id or False,
                             })
        return True
