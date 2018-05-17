# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
import re
from odoo import models, api, _
from odoo.exceptions import Warning


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.onchange('work_email')
    def ValidateEmail(self):
        if self.work_email:
            if re.match("^[-a-zA-Z0  -9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                        self.work_email) is not None:
                new_work_email = self.work_email.lower()
                self.work_email = new_work_email
            else:
                raise Warning(_('Invalid Email '
                                'Please enter a valid email address'))

    @api.model
    def create(self, vals):
        if vals.get('work_email') and vals.get('work_email') != '':
            if not re.\
                    match("^[-a-zA-Z0-9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                          vals.get('work_email')) is not None:
                raise Warning(_('Invalid Email '
                                'Please enter a valid email address'))
        return super(hr_employee, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('work_email') and vals.get('work_email') != '':
            if not re.\
                    match("^[-a-zA-Z0-9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$",
                          vals.get('work_email')) is not None:
                raise Warning(_('Invalid Email '
                                'Please enter a valid email address'))
        return super(hr_employee, self).write(vals)
