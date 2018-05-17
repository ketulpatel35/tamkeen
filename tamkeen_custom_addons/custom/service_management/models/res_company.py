# -*- coding: utf-8 -*-
##############################################################################

from odoo import fields, models


class res_company(models.Model):
    # _name = "res.company"
    _inherit = "res.company"

    admins_group_email = fields.Char(string='Administration Group Email',
                                     default='admins@company.com')
    oe_group_email = fields.Char(
        string='Organization Effectiveness Group Email',
        default='oe@company.com')
    ta_group_email = fields.Char(string='Talent Acquisition Group Email',
                                 default='ta@company.com')
    ss_vp_email = fields.Char(string='Shared Services VP Email',
                              default='ss_vp@company.com')
