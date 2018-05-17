# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char(
        string='Contract Reference', required=False, readonly=True)
    gosi_wage = fields.Float(string='Wage reported to Gosi')
    fixed_allowance = fields.Float(string='Fixed Allowance')

    @api.model
    def create(self, vals):
        if self._context and self._context.get('cr_seq'):
            vals.update({'name': self._context.get('cr_seq')})
        else:
            ref = self.env['ir.sequence'].next_by_code('contract.ref')
            vals.update({'name': ref})
        create_rec = super(hr_contract, self).create(vals)
        return create_rec

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        super(hr_contract, self)._onchange_employee_id()
        if self.employee_id:
            self.f_employee_no = self.employee_id.f_employee_no
