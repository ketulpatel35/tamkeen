# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class EmployeeObjectiveConfigSettings(models.Model):
    _name = 'emp.objective.config.settings'
    _rec_name = 'min_weightage'

    min_weightage = fields.Char(string="Minimum Weightage")
    max_weightage = fields.Char(string="Maximum Weightage")
    min_obj = fields.Char(string="Minimum Objective Per Year")
    max_obj = fields.Char(string="Maximum Objective Per Year")
