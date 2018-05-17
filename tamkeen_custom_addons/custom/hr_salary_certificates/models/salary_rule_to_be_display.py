# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    _order = 'sequence asc'

    display_in_ess = fields.Boolean(string='Display in Self Service('
                                                 'Other)',
                                     copy=False)
    # display_in_ess = fields.Boolean(string='Display in Self Service',
    #                                 copy=False)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """ Override _search to order the results, according to some employee.
        The order is the following

        This override is necessary because those fields are not stored and
        depends on an employee_id given in context. This sort will be done
        when there is an employee_id in context and that no other order has
        been given to the method.
        """
        salary_rule_ids = super(HrSalaryRule, self)._search(
            args, offset=offset, limit=limit, order=order, count=count,
            access_rights_uid=access_rights_uid)
        if self._context.get('salary_certi_emp'):
            employee_rec = self.env['hr.employee'].browse(
                self._context.get('salary_certi_emp'))
            rule_ids = []
            s_rule_ids = []
            if employee_rec:
                if employee_rec.contract_id and \
                        employee_rec.contract_id.struct_id:
                    contract_struct_rec = \
                        employee_rec.contract_id.struct_id._get_parent_structure()
                    for struct in contract_struct_rec:
                        [rule_ids.append(rule_rec.id) for rule_rec in
                         struct.rule_ids if rule_rec.display_in_ess]
                    rule_ids = list(set(rule_ids))
                    rule_ids = self.browse(rule_ids).sorted(key=lambda r:
                    r.sequence).ids
                    s_rule_ids = rule_ids[:]
                    if self._context.get('salary_rule_ids'):
                        for r_id in rule_ids:
                            if r_id in self._context.get('salary_rule_ids')[0][2]:
                                s_rule_ids.remove(r_id)
                return s_rule_ids
        return salary_rule_ids
