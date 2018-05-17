from odoo import api, models, fields


class ServiceLog(models.Model):
    _inherit = 'service.log'

    coc_request_id = fields.Many2one('certificate.of.completion',
                                     string='Certificate of Completion '
                                            'Requests')
