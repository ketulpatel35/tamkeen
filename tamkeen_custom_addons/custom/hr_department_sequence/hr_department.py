# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import fields, models, api


class HrDepartment(models.Model):

    _inherit = 'hr.department'

    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence',
                              help="Gives the sequence order"
                                   " when displaying a list of departments.")
    parent_id = fields.Many2one('hr.department',
                                string='Parent Department',
                                ondelete='cascade')
    parent_left = fields.Integer(string='Left Parent', index=True)
    parent_right = fields.Integer(string='Right Parent', index=True)

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'
    _sql_constraints = [
        ('code_uniq',
         'unique(code, company_id)',
         'The code for the department must be unique per company !'),
    ]

    @api.multi
    def name_get(self):
        """
        Show department code with name
        """
        return [(record.id,
                 '[%s] %s' % (record.code, record.name)
                 if record.code else record.name)
                for record in self]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        department = self\
            .search(['|',
                     ('code', 'ilike', name),
                     ('name', 'ilike', name)] + args, limit=limit)
        return department.name_get()
