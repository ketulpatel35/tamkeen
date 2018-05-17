from odoo import models, api, fields


class ResCompany(models.Model):
    _inherit = 'res.company'


    leave_type_id = fields.Many2one('hr.holidays.status',
                                         string='Default Leave Type')