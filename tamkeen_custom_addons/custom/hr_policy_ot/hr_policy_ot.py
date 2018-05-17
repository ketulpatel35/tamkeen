# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from pytz import common_timezones
from odoo import api, fields, models


class policy_ot(models.Model):
    _name = 'hr.policy.ot'

    name = fields.Char(string='Name')
    date = fields.Date(string='Effective Date')
    line_ids = fields.One2many('hr.policy.line.ot', 'policy_id',
                               string='Policy Lines')

    # Return records with latest date first
    _order = 'date desc'

    @api.multi
    def get_codes(self):
        res = []
        [res.append((line.code, line.name, line.type, line.rate))
         for line in self.line_ids]
        return res

    @api.multi
    def daily_codes(self):
        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'daily']
        return res

    @api.multi
    def restday_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'weekly' and
         line.active_after_units == 'day']
        return res

    @api.multi
    def restday2_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'restday']
        return res

    @api.multi
    def weekly_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'weekly' and
         line.active_after_units == 'min']
        return res

    @api.multi
    def holiday_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'holiday']
        return res


class policy_line_ot(models.Model):
    _name = 'hr.policy.line.ot'

    @api.model
    def _tz_list(self):
        res = tuple()
        for name in common_timezones:
            res += ((name, name),)
        return res

    name = fields.Char(string='Name')
    policy_id = fields.Many2one('hr.policy.ot', string='Policy')
    type = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'),
                             ('restday', 'Rest Day'),
                             ('holiday', 'Public Holiday')],
                            string='Type')
    weekly_working_days = fields.Integer(string='Weekly Working Days')
    active_after = fields.Integer(string='Active After', help="Minutes after "
                                                              "which this "
                                                              "policy applies")
    active_start_time = fields.Char(string='Active Start Time',
                                    help="Time in 24 hour time format")
    active_end_time = fields.Char(string='Active End Time',
                                  help="Time in 24 hour time format")
    tz = fields.Selection(_tz_list, string='Time Zone')
    rate = fields.Float(string='Rate',
                        help='Multiplier of employee wage.')
    code = fields.Char(string='Code',
                       help="Use this code in the salary rules.")


class policy_group(models.Model):

    _name = 'hr.policy.group'
    _inherit = 'hr.policy.group'

    ot_policy_ids = fields.Many2many('hr.policy.ot', 'hr_policy_group_ot_rel',
                                     'group_id', 'ot_id',
                                     string='Overtime Policy')
