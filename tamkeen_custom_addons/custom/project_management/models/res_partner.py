from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_project_count(self):
        for partner in self:
            partner.project_count = self.env['project.project'].search_count([
                ('partner_id', '=', partner.id)])

    project_count = fields.Integer(
        compute='_compute_project_count', string="Projects")
    spoc = fields.Boolean(string='SPOC')
