# -*- coding:utf-8 -*-
##############################################################################
from odoo import models, fields


class hr_holidays(models.Model):

    _inherit = 'hr.holidays'

    skip_notifications = fields.Boolean(
        string='Skip Notifications',
        help="Allow the system to stop sending the notifications.")
