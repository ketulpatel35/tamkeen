# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class CrmMilestonesSchedule(models.Model):
    _name = 'crm.milestones.schedule'

    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    name = fields.Char('Action')
    description = fields.Text('Remarks')
    amount = fields.Float('Amount')
    percentage = fields.Float('Percentage')
