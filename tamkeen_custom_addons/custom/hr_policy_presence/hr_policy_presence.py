# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class policy_presence(models.Model):
    _name = 'hr.policy.presence'

    name = fields.Char(string='Name')
    date = fields.Date(string='Effective Date')
    work_days_per_month = fields.Integer(string='Working Days/Month',
                                         default=26)
    line_ids = fields.One2many('hr.policy.line.presence', 'policy_id',
                               string='Policy Lines')

    # Return records with latest date first
    _order = 'date desc'

    @api.multi
    def get_codes(self):
        res = []
        [res.append((line.code, line.name, line.type, line.rate,
                     line.duration))
         for line in self.line_ids]
        return res


class policy_line_presence(models.Model):
    _name = 'hr.policy.line.presence'

    name = fields.Char(string='Name')
    policy_id = fields.Many2one('hr.policy.presence', string='Policy')
    code = fields.Char(string='Code', help="Use this code in the "
                                           "salary rules.")
    rate = fields.Float(string='Rate', default=1.0,
                        help='Multiplier of employee wage.')
    type = fields.Selection([('normal', 'Normal Working Hours'),
                             ('holiday', 'Holidays'),
                             ('restday', 'Rest Days')],
                            string='Type')
    active_after = fields.Integer(string='Active After', help='Minutes after '
                                                              'first punch of '
                                                              'the day in '
                                                              'which policy '
                                                              'will take '
                                                              'effect.')
    duration = fields.Integer(string='Duration', help="In minutes.")


class policy_group(models.Model):

    _name = 'hr.policy.group'
    _inherit = 'hr.policy.group'

    presence_policy_ids = fields.Many2many('hr.policy.presence',
                                           'hr_policy_group_presence_rel',
                                           'group_id', 'presence_id',
                                           string='Presence Policy')
