from odoo import api, fields, models


class Survey(models.Model):
    _inherit = 'survey.survey'

    @api.model
    def _select_objects(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    reference_id = fields.Reference(string='Source Document',
                                    selection='_select_objects')