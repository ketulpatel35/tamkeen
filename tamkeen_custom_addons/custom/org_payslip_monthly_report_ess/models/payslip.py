# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, modules, tools
from datetime import datetime
from odoo.exceptions import Warning
from odoo.http import request
import os
import tempfile
import PythonMagick
import img2pdf
import sys
import PyPDF2

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # @api.multi
    # def get_deduction_data(self):
    #     rule_value_dict = {}
    #     data = self.get_deduction_latest_contract_structure_localdict()
    #     if data:
    #         for rule in self.struct_id.rule_ids:
    #             if rule.category_id.code in ['DED']:
    #                 rule_value_dict.update({rule.code: data[rule.code] or 0.00,
    #                                         })
    #         total = sum(rule_value_dict.values())
    #     rule_value_dict.update({'total': total})
    #     for key, value in rule_value_dict.items():
    #         rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
    #     return rule_value_dict
    #
    # @api.multi
    # def get_deduction_latest_contract_structure_localdict(self):
    #     blacklist = []
    #     for rec in self:
    #         def _sum_salary_rule_category(localdict, category, amount):
    #             if category.parent_id:
    #                 localdict = _sum_salary_rule_category(localdict,
    #                                                       category.parent_id,
    #                                                       amount)
    #             localdict[
    #                 'categories'].dict[category.code] = \
    #                 category.code in localdict['categories'].dict and \
    #                 localdict['categories'].dict[
    #                     category.code] + amount or amount
    #             return localdict
    #
    #         class BrowsableObject(object):
    #
    #             def __init__(self, employee_id, dict, env):
    #                 self.employee_id = employee_id
    #                 self.dict = dict
    #                 self.env = env
    #
    #             def __getattr__(self, attr):
    #                 return attr in self.dict and self.dict.__getitem__(
    #                     attr) or 0.0
    #
    #         rules_dict = {}
    #         current_rule_ids = []
    #         if rec.employee_id.contract_id.struct_id:
    #             contract_struct_rec = rec.employee_id.contract_id.struct_id \
    #                 ._get_parent_structure()
    #             for struct in contract_struct_rec:
    #                 sort_current_rule_ids = struct.rule_ids.ids
    #                 current_rule_ids += list(set(sort_current_rule_ids))
    #         categories = BrowsableObject(rec.employee_id.id, {}, self.env)
    #         rules = BrowsableObject(rec.employee_id.id, rules_dict, self.env)
    #         baselocaldict = {'categories': categories, 'rules': rules}
    #         sorted_rules = rec.struct_id.rule_ids
    #         localdict = dict(baselocaldict, employee=rec.employee_id,
    #                          contract=rec.employee_id.contract_id)
    #         count = 0
    #         for rule in sorted_rules:
    #             if rule.category_id.code in ['DED']:
    #                 localdict['result'] = None
    #                 localdict['result_qty'] = 1.0
    #                 localdict['result_rate'] = 100
    #                 if rule.satisfy_condition(localdict) and rule.id not in \
    #                         blacklist and rule.id in current_rule_ids:
    #                     # compute the amount of the rule
    #                     amount, qty, rate = rule.compute_rule(localdict)
    #                     count += amount
    #                     # check if there is already a rule computed with that code
    #                     previous_amount = rule.code in localdict and localdict[
    #                         rule.code] or 0.0
    #                     # set/overwrite the amount computed for this rule in the
    #                     # localdict
    #                     tot_rule = amount * qty * rate / 100.0
    #                     # if localdict.get(rule.code):
    #                     #     tot_rule += localdict.get(rule.code)
    #                     localdict[rule.code] = tot_rule
    #                     rules_dict[rule.code] = rule
    #                     # sum the amount for its salary category
    #                     localdict = _sum_salary_rule_category(localdict,
    #                                                           rule.category_id,
    #                                                           tot_rule -
    #                                                           previous_amount)
    #         return localdict
    #
    # @api.multi
    # def get_benefit_data(self):
    #     rule_value_dict = {}
    #     data = self.get_benifit_latest_contract_structure_localdict()
    #     if data:
    #         for rule in self.struct_id.rule_ids:
    #             if rule.category_id.code in ['GEN']:
    #                 rule_value_dict.update({rule.code: data[rule.code] or 0.00,
    #                                         })
    #         total = sum(rule_value_dict.values())
    #     rule_value_dict.update({'total': total})
    #     for key, value in rule_value_dict.items():
    #         rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
    #     return rule_value_dict
    #
    # @api.multi
    # def get_benifit_latest_contract_structure_localdict(self):
    #     blacklist = []
    #     for rec in self:
    #         def _sum_salary_rule_category(localdict, category, amount):
    #             if category.parent_id:
    #                 localdict = _sum_salary_rule_category(localdict,
    #                                                       category.parent_id,
    #                                                       amount)
    #             localdict[
    #                 'categories'].dict[category.code] = \
    #                 category.code in localdict['categories'].dict and \
    #                 localdict['categories'].dict[
    #                     category.code] + amount or amount
    #             return localdict
    #
    #         class BrowsableObject(object):
    #
    #             def __init__(self, employee_id, dict, env):
    #                 self.employee_id = employee_id
    #                 self.dict = dict
    #                 self.env = env
    #
    #             def __getattr__(self, attr):
    #                 return attr in self.dict and self.dict.__getitem__(
    #                     attr) or 0.0
    #
    #         rules_dict = {}
    #         current_rule_ids = []
    #         if rec.employee_id.contract_id.struct_id:
    #             contract_struct_rec = rec.employee_id.contract_id.struct_id \
    #                 ._get_parent_structure()
    #             for struct in contract_struct_rec:
    #                 sort_current_rule_ids = struct.rule_ids.ids
    #                 current_rule_ids += list(set(sort_current_rule_ids))
    #         categories = BrowsableObject(rec.employee_id.id, {}, self.env)
    #         rules = BrowsableObject(rec.employee_id.id, rules_dict, self.env)
    #         baselocaldict = {'categories': categories, 'rules': rules}
    #         sorted_rules = rec.struct_id.rule_ids
    #         localdict = dict(baselocaldict, employee=rec.employee_id,
    #                          contract=rec.employee_id.contract_id)
    #         count = 0
    #         for rule in sorted_rules:
    #             if rule.category_id.code in ['GEN']:
    #                 localdict['result'] = None
    #                 localdict['result_qty'] = 1.0
    #                 localdict['result_rate'] = 100
    #                 if rule.satisfy_condition(localdict) and rule.id not in \
    #                         blacklist and rule.id in current_rule_ids:
    #                     # compute the amount of the rule
    #                     amount, qty, rate = rule.compute_rule(localdict)
    #                     count += amount
    #                     # check if there is already a rule computed with that code
    #                     previous_amount = rule.code in localdict and localdict[
    #                         rule.code] or 0.0
    #                     # set/overwrite the amount computed for this rule in the
    #                     # localdict
    #                     tot_rule = amount * qty * rate / 100.0
    #                     # if localdict.get(rule.code):
    #                     #     tot_rule += localdict.get(rule.code)
    #                     localdict[rule.code] = tot_rule
    #                     rules_dict[rule.code] = rule
    #                     # sum the amount for its salary category
    #                     localdict = _sum_salary_rule_category(localdict,
    #                                                           rule.category_id,
    #                                                           tot_rule -
    #                                                           previous_amount)
    #         return localdict
    #
    # @api.multi
    # def get_data(self):
    #     rule_value_dict = {}
    #     data = self.get_latest_contract_structure_localdict()
    #     if data:
    #         for rule in self.struct_id.rule_ids:
    #             if rule.category_id.code in ['ALW', 'BASIC']:
    #                 rule_value_dict.update({rule.code: data[rule.code] or 0.00,
    #                 })
    #         total = sum(rule_value_dict.values())
    #     rule_value_dict.update({'total': total})
    #     for key, value in rule_value_dict.items():
    #         rule_value_dict.update({key: '{:0.2f}'.format(abs(value))})
    #     return rule_value_dict
    #
    # @api.multi
    # def get_latest_contract_structure_localdict(self):
    #     blacklist = []
    #     for rec in self:
    #         def _sum_salary_rule_category(localdict, category, amount):
    #             if category.parent_id:
    #                 localdict = _sum_salary_rule_category(localdict,
    #                                                       category.parent_id,
    #                                                       amount)
    #             localdict[
    #                 'categories'].dict[category.code] = \
    #                 category.code in localdict['categories'].dict and \
    #                 localdict['categories'].dict[
    #                     category.code] + amount or amount
    #             return localdict
    #
    #         class BrowsableObject(object):
    #
    #             def __init__(self, employee_id, dict, env):
    #                 self.employee_id = employee_id
    #                 self.dict = dict
    #                 self.env = env
    #
    #             def __getattr__(self, attr):
    #                 return attr in self.dict and self.dict.__getitem__(
    #                     attr) or 0.0
    #
    #         rules_dict = {}
    #         current_rule_ids = []
    #         if rec.employee_id.contract_id.struct_id:
    #             contract_struct_rec = rec.employee_id.contract_id.struct_id \
    #                 ._get_parent_structure()
    #             for struct in contract_struct_rec:
    #                 sort_current_rule_ids = struct.rule_ids.ids
    #                 current_rule_ids += list(set(sort_current_rule_ids))
    #         categories = BrowsableObject(rec.employee_id.id, {}, self.env)
    #         rules = BrowsableObject(rec.employee_id.id, rules_dict, self.env)
    #         baselocaldict = {'categories': categories, 'rules': rules}
    #         sorted_rules = rec.struct_id.rule_ids
    #         localdict = dict(baselocaldict, employee=rec.employee_id,
    #                          contract=rec.employee_id.contract_id)
    #         count = 0
    #         for rule in sorted_rules:
    #             if rule.category_id.code in ['ALW', 'BASIC']:
    #                 localdict['result'] = None
    #                 localdict['result_qty'] = 1.0
    #                 localdict['result_rate'] = 100
    #                 if rule.satisfy_condition(localdict) and rule.id not in \
    #                         blacklist and rule.id in current_rule_ids:
    #                     # compute the amount of the rule
    #                     amount, qty, rate = rule.compute_rule(localdict)
    #                     count += amount
    #                     # check if there is already a rule computed with that code
    #                     previous_amount = rule.code in localdict and localdict[
    #                         rule.code] or 0.0
    #                     # set/overwrite the amount computed for this rule in the
    #                     # localdict
    #                     tot_rule = amount * qty * rate / 100.0
    #                     # if localdict.get(rule.code):
    #                     #     tot_rule += localdict.get(rule.code)
    #                     localdict[rule.code] = tot_rule
    #                     rules_dict[rule.code] = rule
    #                     # sum the amount for its salary category
    #                     localdict = _sum_salary_rule_category(localdict,
    #                                                           rule.category_id,
    #                                                           tot_rule -
    #                                                           previous_amount)
    #         return localdict

    @api.model
    def get_current_date(self):
        """
        get current date
        :return:
        """
        return datetime.today().date()

