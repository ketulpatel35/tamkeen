# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class policy_absence(models.Model):
    _name = 'hr.policy.absence'

    name = fields.Char(string='Name')
    date = fields.Date(string='Effective Date')
    line_ids = fields.One2many('hr.policy.line.absence', 'policy_id',
                               string='Policy Lines')

    # Return records with latest date first
    _order = 'date desc'

    @api.multi
    def get_codes(self):

        res = []
        [res.append((line.code, line.name, line.type, line.rate,
                     line.use_awol))
         for line in self.line_ids]
        return res

    @api.multi
    def paid_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'paid']
        return res

    @api.multi
    def unpaid_codes(self):

        res = []
        [res.append((line.code, line.name))
         for line in self.line_ids if line.type == 'unpaid']
        return res


class policy_line_absence(models.Model):
    _name = 'hr.policy.line.absence'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code',
                       help="Use this code in the salary rules.")
    holiday_status_id = fields.Many2one('hr.holidays.status', string='Leave')
    policy_id = fields.Many2one('hr.policy.absence', string='Policy')
    type = fields.Selection([('paid', 'Paid'),
                             ('unpaid', 'Unpaid'),
                             ('dock', 'Dock')],
                            string='Type',
                            help="Determines how the absence will be treated "
                                 "in payroll. The 'Dock Salary' type will "
                                 "deduct money "
                                 "(usefull for salaried employees).")
    rate = fields.Float(strring='Rate', help='Multiplier of employee wage.')
    use_awol = fields.Boolean(string='Absent Without Leave',
                              help='Use this policy to record employee time '
                                   'absence not covered by other leaves.')

    @api.onchange('holiday_status_id')
    def onchange_holiday(self):
        if self.holiday_status_id:
            self.name = self.holiday_status_id.name
            self.code = self.holiday_status_id.code


class policy_group(models.Model):

    _name = 'hr.policy.group'
    _inherit = 'hr.policy.group'

    absence_policy_ids = fields.Many2many('hr.policy.absence',
                                          'hr_policy_group_absence_rel',
                                          'group_id', 'absence_id',
                                          string='Absence Policy')
