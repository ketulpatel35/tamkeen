from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    coc_policy_id = fields.Many2one('service.configuration.panel',
                                    string='Certificate of Completion')
