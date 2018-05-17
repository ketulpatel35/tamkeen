from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    overtime_policy_id = fields.Many2one('service.configuration.panel',
                                         string='Overtime Policy')
