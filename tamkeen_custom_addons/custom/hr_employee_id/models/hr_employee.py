# -*- coding: utf-8 -*-
# © 2011, 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>
# © 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class HrEmployee(models.Model):
    """Implement company wide unique identification number."""
    IDLEN = 8
    _inherit = 'hr.employee'

    employee_no = fields.Char(string='SS-Employee ID',
                              size=IDLEN,
                              readonly=False, copy=False)
    f_employee_no = fields.Char(string='Employee Company ID',
                                size=IDLEN + 2,
                                readonly=False, copy=False)
    tin_no = fields.Char(string='TIN No')

    sql_constraints = [
        ('femployeeno_uniq', 'UNIQUE(f_employee_no)',
         'The Employee Company ID must be unique accross the company(s).')
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        records = self.search(
            ['|', ('f_employee_no', operator, name), ('name', operator, name)] + args,
            limit=limit)
        return records.name_get()

    @api.multi
    def name_get(self):
        """
        name should display with code
        :return:
        """
        res = []
        for record in self:
            f_employee_no = record.f_employee_no or ''
            name = record.name or ''
            display_name = '[ ' + f_employee_no + ' ] ' + name
            res.append((record.id, display_name))
        return res
