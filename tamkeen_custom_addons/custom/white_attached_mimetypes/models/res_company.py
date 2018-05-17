# -*- encoding: utf-8 -*-
from odoo import fields, models


class res_company(models.Model):

    _inherit = "res.company"

    attachment_size = fields.Float(
        string="Maximum Attachmant Size(MB)",
        default=10,
        help="Maximum size of attachment allowed to upload,"
             "i.e 5 represent by 5MB")
