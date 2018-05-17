# -*- coding: utf-8 -*-
##############################################################################
from odoo import fields, models, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def get_latest_contract_structure_localdict(self, emp):
        blacklist = []
        for rec in self:
            def _sum_salary_rule_category(localdict, category, amount):
                if category.parent_id:
                    localdict = _sum_salary_rule_category(localdict,
                                                          category.parent_id,
                                                          amount)
                localdict[
                    'categories'].dict[category.code] = \
                    category.code in localdict['categories'].dict and \
                    localdict['categories'].dict[
                        category.code] + amount or amount
                return localdict

            class BrowsableObject(object):

                def __init__(self, employee_id, dict, env):
                    self.employee_id = employee_id
                    self.dict = dict
                    self.env = env

                def __getattr__(self, attr):
                    return attr in self.dict and self.dict.__getitem__(
                        attr) or 0.0

            rules_dict = {}
            current_rule_ids = []
            sorted_rules_new = []
            if emp.contract_id and emp.contract_id.struct_id:
                contract_struct_rec = emp.contract_id.struct_id \
                    ._get_parent_structure()
                for struct in contract_struct_rec:
                    sort_current_rule_ids = struct.rule_ids.ids
                    current_rule_ids += list(set(sort_current_rule_ids))
            categories = BrowsableObject(emp.id, {}, self.env)
            rules = BrowsableObject(emp.id, rules_dict, self.env)
            baselocaldict = {'categories': categories, 'rules': rules}
            sorted_rules = list(set(emp.contract_id.struct_id.rule_ids.ids + \
                                    current_rule_ids))
            sorted_rules = self.env['hr.salary.rule'].browse(sorted_rules)
            for rule in sorted_rules:
                if rule.code in ('BASIC', 'HA', 'TA'):
                    sorted_rules_new.append(rule)
                if rule.category_id.code == 'ALW' and rule not in \
                        sorted_rules_new:
                    sorted_rules_new.append(rule)
            localdict = dict(baselocaldict, employee=emp,
                             contract=emp.contract_id)
            count = 0
            all_alowances = 0.0
            for rule in sorted_rules_new:
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                if rule.satisfy_condition(localdict) and rule.id not in \
                        blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    count += amount
                    if rule.category_id.code == 'ALW':
                        all_alowances += amount
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[
                        rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    tot_rule = amount * qty * rate / 100.0
                    # if localdict.get(rule.code):
                    #     tot_rule += localdict.get(rule.code)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict,
                                                          rule.category_id,
                                                          tot_rule -
                                                          previous_amount)
            localdict.update({'all_allowances': all_alowances})
            return localdict

    @api.model
    def get_employee_salary_info(self):
        """
        get employee salary information
        :return:
        """
        localdict = self.get_latest_contract_structure_localdict(
            self.employee_id)
        salary_info = []
        if self.struct_id:
            for rule_rec in self.struct_id.rule_ids:
                salary_data = {'name': rule_rec.name, 'code': rule_rec.code,
                               'hr_contract_id': self.id}
                amount_tuple = rule_rec.compute_rule(localdict)
                salary_data.update({'amount': amount_tuple[0]})
                salary_info.append(salary_data)
        return salary_info

    @api.depends('wage', 'struct_id')
    def get_salary_breakup(self):
        """
        :return:
        """
        for rec in self:
            # remove stash
            salary_breakup_rec = False
            for x in rec.salary_breakup_ids:
                rec.salary_breakup_ids = (2, x.id)
            salary_info = rec.get_employee_salary_info()
            for s_info in salary_info:
                n_rec = self.env['salary.breakup'].create(s_info)
                if not salary_breakup_rec:
                    salary_breakup_rec = n_rec
                else:
                    salary_breakup_rec += n_rec
            self.salary_breakup_ids = salary_breakup_rec

    salary_breakup_ids = fields.One2many('salary.breakup', 'hr_contract_id',
                                         compute='get_salary_breakup')
