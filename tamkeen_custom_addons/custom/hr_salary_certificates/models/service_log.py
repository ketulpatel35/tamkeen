# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class SalaryCertificatesServiceLog(models.Model):
    _name = 'salary.certificates.service.log'

    salary_certificates_id = fields.Many2one('emp.salary.certificates', copy=False)
    user_id = fields.Many2one('res.users', string='User', copy=False)
    activity_datetime = fields.Datetime(string='Activity Datetime', copy=False)
    state_from = fields.Char(string='State From', copy=False)
    state_to = fields.Char(string='State To', copy=False)
    reason = fields.Text(string='Reason', copy=False)